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
from rest_framework import permissions
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from blueapps.account.decorators import login_exempt

from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.services.bpf_service.api.serializers import StandardResponseSerializer

logger = logging.getLogger("root")


class DetailResponseSerializer(StandardResponseSerializer):
    class DetailDataSerializer(serializers.Serializer):
        class SchemaSerializer(serializers.Serializer):
            class PropertySerializer(serializers.Serializer):
                title = serializers.CharField(help_text="字段名")
                type = serializers.CharField(help_text="字段类型")
                description = serializers.CharField(help_text="字段描述")
                default = serializers.CharField(help_text="默认值")

            type = serializers.CharField(help_text="字段类型")
            properties = PropertySerializer(help_text="字段详情")
            required = serializers.ListField(help_text="必填字段", child=serializers.CharField(help_text="字段 key"))
            definitions = serializers.DictField(help_text="引用对象详情，结构同 SchemaSerializer")

        class InputsFieldsSerializer(SchemaSerializer):
            pass

        class ContextInputsFieldsSerializer(SchemaSerializer):
            pass

        class OutputsFieldsSerializer(SchemaSerializer):
            pass

        class DetailFormsSerializer(serializers.Serializer):
            renderform = serializers.CharField(help_text="renderform 表单数据")

        version = serializers.CharField(help_text="版本号")
        inputs = InputsFieldsSerializer(help_text="输入模型")
        context_inputs = ContextInputsFieldsSerializer(help_text="上下文输入模型")
        outputs = OutputsFieldsSerializer(help_text="输出模型")
        forms = DetailFormsSerializer(help_text="表单数据")

    data = DetailDataSerializer(help_text="接口数据")


@method_decorator(login_exempt, name="dispatch")
class Detail(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        method="GET",
        operation_summary="Get plugin detail for specific version",
        responses={200: DetailResponseSerializer},
    )
    @action(methods=["GET"], detail=True)
    def get(self, request, version):
        plugin_cls = VersionHub.all_plugins().get(version)
        if not plugin_cls:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({"result": True, "data": plugin_cls.dict(), "message": ""})
