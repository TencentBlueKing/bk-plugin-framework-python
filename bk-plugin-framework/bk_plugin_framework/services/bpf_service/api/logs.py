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

from apigw_manager.drf.utils import gen_apigateway_resource_config
from blueapps.account.decorators import login_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from bk_plugin_framework.runtime.loghub.models import LogEntry
from bk_plugin_framework.serializers import standard_response_enveloper
from bk_plugin_framework.services.bpf_service.api.serializers import (
    StandardResponseSerializer,
)

logger = logging.getLogger("root")


class LogsResponseSerializer(StandardResponseSerializer):
    class LogsDataSerializer(serializers.Serializer):
        class Meta:
            ref_name = "log"

        log = serializers.CharField(help_text="日志内容")

    data = LogsDataSerializer(help_text="接口数据")


@method_decorator(login_exempt, name="dispatch")
class Logs(APIView):

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="获取插件执行日志",
        operation_id="plugin_logs",
        responses={200: standard_response_enveloper(LogsResponseSerializer)},
        extensions=gen_apigateway_resource_config(
            is_public=True,
            allow_apply_permission=True,
            user_verified_required=True,
            app_verified_required=True,
            resource_permission_required=True,
            description_en="Get plugin execution log with trace_id",
            match_subpath=False,
        ),
    )
    @action(methods=["GET"], detail=True)
    def get(self, request, trace_id):
        return Response({"result": True, "data": {"log": LogEntry.objects.get_plain_log(trace_id)}, "message": ""})
