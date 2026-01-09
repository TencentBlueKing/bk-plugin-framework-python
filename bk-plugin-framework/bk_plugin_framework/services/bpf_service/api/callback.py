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

import json
import logging
import traceback

from apigw_manager.apigw.decorators import apigw_require
from apigw_manager.drf.utils import gen_apigateway_resource_config
from blueapps.account.decorators import login_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from bk_plugin_framework.runtime.callback.api import callback, parse_callback_token
from bk_plugin_framework.serializers import standard_response_enveloper

logger = logging.getLogger("bk_plugin")


class PluginCallbackParamsSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="插件回调token", required=True)


class PluginCallbackResponseSerializer(serializers.Serializer):
    result = serializers.BooleanField(help_text="回调结果，True表示成功，False表示失败")
    message = serializers.CharField(help_text="回调结果信息", required=False)


@method_decorator(login_exempt, name="dispatch")
@method_decorator(apigw_require, name="dispatch")
class PluginCallback(APIView):
    authentication_classes = []  # csrf exempt

    @extend_schema(
        summary="插件回调",
        operation_id="callback",
        request=PluginCallbackParamsSerializer,
        responses={200: standard_response_enveloper(PluginCallbackResponseSerializer)},
        extensions=gen_apigateway_resource_config(
            is_public=True,
            allow_apply_permission=True,
            user_verified_required=True,
            app_verified_required=True,
            resource_permission_required=True,
            description_en="plugin callback",
            match_subpath=False,
        ),
    )
    @action(methods=["POST"], detail=True)
    def post(self, request, token):
        logger.info("[plugin callback]token=({}),body={}".format(token, request.body))

        parse_result = parse_callback_token(token)

        if not parse_result["result"]:
            logger.warning(parse_result["message"])
            return Response(parse_result, status=400)

        try:
            callback_data = json.loads(request.body)
        except Exception:
            logger.warning("node callback error: %s" % traceback.format_exc())
            return Response({"result": False, "message": "invalid request body"}, status=400)
        parse_data = parse_result["data"]
        callback_result = callback(parse_data["trace_id"], parse_data["callback_id"], callback_data)

        if not callback_result["result"]:
            logger.warning(callback_result["message"])
            return Response(callback_result, status=400)

        return Response(callback_result, status=200)
