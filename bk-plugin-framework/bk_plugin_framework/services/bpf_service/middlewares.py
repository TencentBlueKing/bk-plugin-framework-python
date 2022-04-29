# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import uuid

from bk_plugin_framework.utils import local
from bk_plugin_framework.envs import settings


class TraceIDInjectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.trace_id = uuid.uuid4().hex
        local.set_trace_id(request.trace_id)
        response = self.get_response(request)
        return response


class TokenInjectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.BKPAAS_ENVIRONMENT == "dev":
            request.token = request.COOKIES.get(settings.USER_TOKEN_KEY_NAME, "")
        elif not hasattr(request, "token"):
            request.token = request.META.get("HTTP_X_BKAPI_JWT", "")

        response = self.get_response(request)
        return response
