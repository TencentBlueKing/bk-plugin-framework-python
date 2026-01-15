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

from apigw_manager.drf.utils import gen_apigateway_resource_config
from blueapps.account.decorators import login_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from bk_plugin_framework.runtime.schedule.models import Schedule as ScheduleModel
from bk_plugin_framework.serializers import standard_response_enveloper
from bk_plugin_framework.services.bpf_service.api.serializers import (
    StandardResponseSerializer,
)

logger = logging.getLogger("root")


class ScheduleParamsSerializer(serializers.Serializer):
    trace_id = serializers.CharField(help_text="插件调用 trace id")


class ScheduleResponseSerializer(StandardResponseSerializer):
    class ScheduleDataSerializer(serializers.Serializer):
        class Meta:
            ref_name = "schedule"

        trace_id = serializers.CharField(help_text="插件调用 trace id")
        plugin_version = serializers.CharField(help_text="插件版本")
        state = serializers.IntegerField(help_text="插件执行状态(2: POLL 3:CALLBACK 4:SUCCESS 5:FAIL)")
        outputs = serializers.DictField(help_text="插件输出")
        err = serializers.CharField(help_text="错误信息")
        created_at = serializers.CharField(help_text="创建时间")
        finish_at = serializers.CharField(help_text="结束时间")

    data = ScheduleDataSerializer(help_text="接口数据")


@method_decorator(login_exempt, name="dispatch")
class Schedule(APIView):

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="获取插件调度详情",
        operation_id="plugin_schedule",
        parameters=[ScheduleParamsSerializer],
        responses={200: standard_response_enveloper(ScheduleResponseSerializer)},
        extensions=gen_apigateway_resource_config(
            is_public=True,
            allow_apply_permission=True,
            user_verified_required=True,
            app_verified_required=True,
            resource_permission_required=True,
            description_en="Get plugin schedule detail with trace_id",
            match_subpath=False,
        ),
    )
    @action(methods=["GET"], detail=True)
    def get(self, request, trace_id):
        try:
            s = ScheduleModel.objects.get(trace_id=trace_id)
        except ScheduleModel.DoesNotExist:
            return Response(
                {
                    "result": False,
                    "data": None,
                    "message": "can not find schedule for trace_id %s" % trace_id,
                    "trace_id": request.trace_id,
                }
            )

        try:
            outputs = json.loads(s.data)["outputs"]
        except Exception as e:
            logging.exception("outputs fetch with trace_id %s error" % trace_id)
            return Response(
                {
                    "result": False,
                    "data": None,
                    "message": "outputs fetch with trace_id {} error: {}".format(trace_id, str(e)),
                    "trace_id": request.trace_id,
                }
            )

        return Response(
            {
                "result": True,
                "data": {
                    "trace_id": trace_id,
                    "plugin_version": s.plugin_version,
                    "state": s.state,
                    "outputs": outputs,
                    "err": s.err,
                    "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "finish_at": s.finish_at.strftime("%Y-%m-%d %H:%M:%S") if s.finish_at else "",
                },
                "trace_id": request.trace_id,
                "message": "",
            }
        )
