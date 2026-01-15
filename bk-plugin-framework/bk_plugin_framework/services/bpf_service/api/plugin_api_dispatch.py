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
import json
import logging
import re

from urllib.parse import urlsplit
from django.test import RequestFactory
from django.urls import resolve, Resolver404
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

from bk_plugin_framework.services.bpf_service.api.permissions import ScopeAllowPermission
from bk_plugin_framework.services.bpf_service.api.serializers import StandardResponseSerializer

logger = logging.getLogger("bk_plugin")

CUSTOM_REQUEST_HEADER_REGEX = re.compile("HTTP_BK_PLUGIN_*")


class PluginAPIDispatchParamsSerializer(serializers.Serializer):
    url = serializers.CharField(help_text="数据接口 URL", required=True)
    method = serializers.CharField(help_text="调用方法", required=True)
    username = serializers.CharField(help_text="用户名", required=True)
    data = serializers.DictField(help_text="接口数据", required=False, default={})
    dumped_data = serializers.CharField(help_text="json dumps后的接口数据", required=False)

    def validate(self, values):
        if values.get("dumped_data"):
            values["data"].update(json.loads(values["dumped_data"]))
        return values

    def validate_url(self, value):
        if not value.startswith("/bk_plugin/plugin_api/"):
            raise serializers.ValidationError("url must starts with '/bk_plugin/plugin_api/'")
        return value

    def validate_method(self, value):
        if value.lower() not in {"get", "post"}:
            raise serializers.ValidationError("not supported method: %s, only support get and post method" % value)
        return value


class PluginAPIDispatchResponseSerializer(StandardResponseSerializer):
    trace_id = serializers.CharField(help_text="调用跟踪 ID")
    data = serializers.DictField(help_text="DATA API 返回的数据")


class DummyUser(object):
    def __init__(self, username):
        self.username = username


@method_decorator(login_exempt, name="dispatch")
@method_decorator(apigw_require, name="dispatch")
class PluginAPIDispatch(APIView):
    authentication_classes = []  # csrf exempt
    permission_classes = [ScopeAllowPermission]

    @swagger_auto_schema(
        method="POST",
        operation_summary="Plugin API dispatch",
        request_body=PluginAPIDispatchParamsSerializer,
        responses={200: PluginAPIDispatchResponseSerializer},
    )
    @action(methods=["POST"], detail=True)
    def post(self, request):
        data_serializer = PluginAPIDispatchParamsSerializer(data=request.data)
        try:
            data_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(
                data={"result": False, "data": None, "message": "输入不合法: %s" % e, "trace_id": request.trace_id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data = data_serializer.validated_data
        logger.info("receive dispatch request with params: %s" % request_data)

        try:
            parsed = urlsplit(request_data["url"])
            logger.info("url(%s) parsed: %s" % (request_data["url"], parsed))

            matched = resolve(parsed.path, urlconf=None)
            view_func, kwargs = matched.func, matched.kwargs

            # get custom request headers
            custom_headers = {}
            for key, value in request.META.items():
                if CUSTOM_REQUEST_HEADER_REGEX.match(key):
                    custom_headers[key] = value

            # get apigw jwt info
            custom_headers["HTTP_X_BKAPI_JWT"] = request.META.get("HTTP_X_BKAPI_JWT", "")

            if request.FILES:
                fake_request = getattr(RequestFactory(), request_data["method"].lower())(
                    path=request_data["url"], data=request_data["data"], **custom_headers
                )
                # inject upload FILES
                for f in request.FILES:
                    fake_request.FILES[f] = request.FILES[f]
            else:
                fake_request = getattr(RequestFactory(), request_data["method"].lower())(
                    path=request_data["url"],
                    content_type=request.content_type,
                    data=request_data["data"],
                    **custom_headers
                )

            # inject APIGW jwt
            fake_request.jwt = request.jwt

            # inject user username info
            fake_request._force_auth_user = DummyUser(username=request_data["username"])

            resp = view_func(fake_request, **kwargs)
            return Response({"result": True, "data": resp.data, "message": "success", "trace_id": request.trace_id})

        except Resolver404:
            logger.exception("url(%s) resolve 404" % request_data["url"])
            return Response(
                data={
                    "result": False,
                    "data": None,
                    "message": "404 error: %s" % request_data["url"],
                    "trace_id": request.trace_id,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception("unknow error")
            return Response(
                data={
                    "result": False,
                    "data": None,
                    "message": "unknow error, please contact plugin developers: %s" % e,
                    "trace_id": request.trace_id,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
