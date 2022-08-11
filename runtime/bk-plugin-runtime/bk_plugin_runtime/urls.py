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

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="PluginService API",
        default_version="v1",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^account/", include("blueapps.account.urls")),
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    url(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    url(r"^bk_plugin/", include("bk_plugin_framework.services.bpf_service.urls")),
]


if settings.ENVIRONMENT == "dev":
    from bk_plugin_framework.services.debug_panel.views import debug_panel

    urlpatterns.extend(
        [
            url(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
            url(r"^$", debug_panel, name="debug-panel"),
        ]
    )
else:
    urlpatterns.append(
        url(r"^$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    )
