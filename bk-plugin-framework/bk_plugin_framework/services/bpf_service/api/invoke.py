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

from apigw_manager.apigw.decorators import apigw_require
from apigw_manager.drf.utils import gen_apigateway_resource_config
from blueapps.account.decorators import login_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.runtime.executor import BKPluginExecutor
from bk_plugin_framework.serializers import standard_response_enveloper
from bk_plugin_framework.services.bpf_service.api.permissions import (
    ScopeAllowPermission,
)
from bk_plugin_framework.services.bpf_service.api.serializers import (
    StandardResponseSerializer,
)

logger = logging.getLogger("bk_plugin")


class InvokeParamsSerializer(serializers.Serializer):
    inputs = serializers.DictField(help_text="插件调用参数", required=True)
    context = serializers.DictField(help_text="插件执行上下文", required=True)


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

    @extend_schema(
        summary="调用指定版本插件",
        operation_id="invoke",
        request=InvokeParamsSerializer,
        responses={200: standard_response_enveloper(InvokeResponseSerializer)},
        extensions=gen_apigateway_resource_config(
            is_public=True,
            allow_apply_permission=True,
            user_verified_required=True,
            app_verified_required=True,
            resource_permission_required=True,
            description_en="Invoke specific version plugin",
            match_subpath=False,
        ),
    )
    @action(methods=["POST"], detail=True)
    def post(self, request, version):
        plugin_cls = VersionHub.all_plugins().get(version)
        if not plugin_cls:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data_serializer = InvokeParamsSerializer(data=request.data)
        try:
            data_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                data={"result": False, "data": None, "message": "输入不合法: %s" % e},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request_data = data_serializer.validated_data

        executor = BKPluginExecutor(trace_id=request.trace_id)

        try:
            execute_result = executor.execute(
                plugin_cls=plugin_cls, inputs=request_data["inputs"], context_inputs=request_data["context"]
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
