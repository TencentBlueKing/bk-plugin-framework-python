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

from django.utils.decorators import method_decorator
from django.conf import settings as default_settings
from rest_framework.views import APIView
from rest_framework.request import Request
from bkoauth import get_app_access_token
from apigw_manager.apigw.decorators import apigw_require

from bk_plugin_framework.envs import settings
from bk_plugin_framework.kit.decorators import login_exempt, inject_user_token
from bk_plugin_framework.kit.authentication import CsrfExemptSessionAuthentication

custom_authentication_classes = (
    [
        CsrfExemptSessionAuthentication,
    ]
    if settings.BKPAAS_ENVIRONMENT == "dev"
    else []
)


@method_decorator(login_exempt, name="dispatch")
@method_decorator(apigw_require, name="dispatch")
@method_decorator(inject_user_token, name="dispatch")
class PluginAPIView(APIView):
    authentication_classes = custom_authentication_classes

    @staticmethod
    def get_bkapi_authorization_info(request: Request) -> str:
        auth_info = {
            "bk_app_code": default_settings.BK_APP_CODE,
            "bk_app_secret": default_settings.BK_APP_SECRET,
            settings.USER_TOKEN_KEY_NAME: request.token,
        }
        if settings.BKPAAS_ENVIRONMENT != "dev":
            access_token = get_app_access_token().access_token
            auth_info.update({"access_token": access_token})

        return json.dumps(auth_info)
