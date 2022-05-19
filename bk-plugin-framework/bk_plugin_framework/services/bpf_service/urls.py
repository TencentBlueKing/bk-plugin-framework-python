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

import sys
import importlib

from django.urls import path, include
from bk_plugin_framework.services.bpf_service import api
from bk_plugin_framework.envs import settings

PLUGIN_API_URLS_MODULE = "bk_plugin.apis.urls"

urlpatterns = [
    path(r"meta/", api.Meta.as_view()),
    path(r"detail/<str:version>", api.Detail.as_view()),
    path(r"invoke/<str:version>", api.Invoke.as_view()),
    path(r"schedule/<str:trace_id>", api.Schedule.as_view()),
    path(r"plugin_api_dispatch/", api.PluginAPIDispatch.as_view()),
    path(r"callback/<str:token>/", api.PluginCallback.as_view()),
]

# add log api
if settings.BKPAAS_ENVIRONMENT == "dev":
    urlpatterns.append(path(r"logs/<str:trace_id>", api.Logs.as_view()))

# add plugin api
try:
    importlib.import_module(PLUGIN_API_URLS_MODULE)
except ModuleNotFoundError:
    sys.stdout.write("[!]can not find plugin api urls module, skip it\n")
else:
    sys.stdout.write("[!]plugin api urls module found\n")
    urlpatterns.append(path(r"plugin_api/", include(PLUGIN_API_URLS_MODULE)))
