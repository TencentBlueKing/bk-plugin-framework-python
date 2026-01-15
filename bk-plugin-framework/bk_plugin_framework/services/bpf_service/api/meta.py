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
from importlib import import_module

from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework import permissions
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from blueapps.account.decorators import login_exempt


from bk_plugin_framework import __version__ as bpf_version
from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.services.bpf_service.api.serializers import StandardResponseSerializer

logger = logging.getLogger("root")

FRAMEWORK_VERSION = bpf_version.__version__
RUNTIME_VERSION = None

try:
    from bk_plugin_runtime import __version__ as bpr_version
except ImportError:
    pass
else:
    RUNTIME_VERSION = bpr_version.__version__


class MetaResponseSerializer(StandardResponseSerializer):
    class MetaDataSerializer(serializers.Serializer):
        class Meta:
            ref_name = "meta"

        code = serializers.CharField(help_text="插件唯一标识")
        description = serializers.CharField(help_text="插件描述信息")
        versions = serializers.ListField(help_text="版本列表", child=serializers.CharField(help_text="版本号"))
        language = serializers.CharField(help_text="插件开发语言")
        framework_version = serializers.CharField(help_text="插件框架版本")
        runtime_version = serializers.CharField(help_text="插件运行时版本")

    data = MetaDataSerializer(help_text="接口数据")


@method_decorator(login_exempt, name="dispatch")
class Meta(APIView):

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        method="GET",
        operation_summary="Get plugin meta info",
        responses={200: MetaResponseSerializer},
    )
    @action(methods=["GET"], detail=True)
    def get(self, request):
        try:
            meta_module = import_module("bk_plugin.meta")
        except ImportError:
            description = ""
            allow_scope = {}
        else:
            description = getattr(meta_module, "description", "")
            allow_scope = getattr(meta_module, "allow_scope", {})

        return Response(
            {
                "result": True,
                "data": {
                    "code": settings.APP_CODE,
                    "versions": VersionHub.versions(),
                    "language": "python",
                    "description": description,
                    "framework_version": FRAMEWORK_VERSION,
                    "runtime_version": RUNTIME_VERSION,
                    "allow_scope": allow_scope,
                },
                "message": "",
            }
        )
