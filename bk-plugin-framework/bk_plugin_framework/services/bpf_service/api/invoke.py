# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - PaaS平台 (BlueKing - PaaS System) available.
Copyright (C) 2022 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import logging

from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from blueapps.account.decorators import login_exempt
from apigw_manager.apigw.decorators import apigw_require


from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.runtime.executor import BKPluginExecutor
from bk_plugin_framework.services.bpf_service.api.permissions import ScopeAllowPermission
from bk_plugin_framework.services.bpf_service.api.serializers import StandardResponseSerializer
from bk_plugin_framework.kit.plugin import Credential

logger = logging.getLogger("bk_plugin")


class InvokeParamsSerializer(serializers.Serializer):
    inputs = serializers.DictField(help_text="插件调用参数", required=True)
    context = serializers.DictField(help_text="插件执行上下文", required=True)
    credentials = serializers.DictField(help_text="插件凭证", required=False, allow_null=True)

    def validate(self, attrs):
        """验证凭证是否提供"""
        plugin_cls = self.context.get("plugin_cls")
        if not plugin_cls:
            return attrs

        # Check if plugin requires credentials (class attribute, similar to ContextInputs)
        credentials_list = []
        credentials_cls = getattr(plugin_cls, "Credentials", None)
        if credentials_cls:
            # Extract all Credential instances from Credentials class
            for attr_name in dir(credentials_cls):
                if attr_name.startswith("_"):
                    continue
                attr_value = getattr(credentials_cls, attr_name)
                if isinstance(attr_value, Credential):
                    credentials_list.append(attr_value)

        if credentials_list:
            # Verify that credentials is provided at top level
            credentials = attrs.get("credentials")

            # Check if credentials is a dict
            if not isinstance(credentials, dict):
                credential_names = [c.name or c.key for c in credentials_list]
                raise serializers.ValidationError(
                    f"该插件需要凭证（{', '.join(credential_names)}），请在请求中提供 credentials 字典"
                )

            # Check each required credential
            missing_credentials = []
            for cred_def in credentials_list:
                # Check if key exists and value is not None or empty string
                if (
                    cred_def.key not in credentials
                    or credentials.get(cred_def.key) is None
                    or credentials.get(cred_def.key) == ""
                ):
                    missing_credentials.append(cred_def.name or cred_def.key)

            if missing_credentials:
                raise serializers.ValidationError(
                    f"该插件需要以下凭证：{', '.join(missing_credentials)}，请在 credentials 中提供这些字段"
                )

        return attrs


class InvokeResponseSerializer(StandardResponseSerializer):
    class InvokeDataSerializer(serializers.Serializer):

        outputs = serializers.DictField(help_text="插件输出数据")
        state = serializers.IntegerField(help_text="插件执行状态(2: POLL 3:CALLBACK 4:SUCCESS 5:FAIL)")
        err = serializers.CharField(help_text="错误信息")

    trace_id = serializers.CharField(help_text="调用跟踪 ID")
    data = InvokeDataSerializer(help_text="接口数据")


@method_decorator(login_exempt, name="dispatch")
@method_decorator(apigw_require, name="dispatch")
class Invoke(APIView):

    authentication_classes = []  # csrf exempt
    permission_classes = [ScopeAllowPermission]

    @swagger_auto_schema(
        method="POST",
        operation_summary="Invoke specific version plugin",
        request_body=InvokeParamsSerializer,
        responses={200: InvokeResponseSerializer},
    )
    @action(methods=["POST"], detail=True)
    def post(self, request, version):
        plugin_cls = VersionHub.all_plugins().get(version)
        if not plugin_cls:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data_serializer = InvokeParamsSerializer(data=request.data, context={"plugin_cls": plugin_cls})
        try:
            data_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                data={"result": False, "data": None, "message": "输入不合法: %s" % e, "trace_id": request.trace_id},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request_data = data_serializer.validated_data

        # Extract credentials from request data
        credentials = request_data.get("credentials") or {}

        executor = BKPluginExecutor(trace_id=request.trace_id)

        try:
            execute_result = executor.execute(
                plugin_cls=plugin_cls,
                inputs=request_data["inputs"],
                context_inputs=request_data["context"],
                credentials=credentials,
            )
        except Exception as e:
            logging.exception("executor execute raise error")
            return Response(
                {
                    "result": False,
                    "data": None,
                    "message": "executor execute raise error: %s" % str(e),
                    "trace_id": request.trace_id,
                }
            )

        return Response(
            {
                "result": True,
                "data": {
                    "outputs": execute_result.outputs,
                    "state": execute_result.state.value,
                    "err": execute_result.err,
                },
                "message": "success",
                "trace_id": request.trace_id,
            }
        )
