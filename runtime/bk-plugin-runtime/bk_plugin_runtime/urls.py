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
from django.contrib import admin
from django.urls import include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^account/", include("blueapps.account.urls")),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    re_path(r"^schema/$", SpectacularAPIView.as_view(), name="schema"),
    re_path(r"^redoc/$", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    re_path(r"^bk_plugin/", include("bk_plugin_framework.services.bpf_service.urls")),
]


if settings.ENVIRONMENT == "dev":
    from bk_plugin_framework.services.debug_panel.views import debug_panel

    urlpatterns.extend(
        [
            re_path(r"^swagger/$", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            re_path(r"^$", debug_panel, name="debug-panel"),
        ]
    )
else:
    urlpatterns.append(
        re_path(r"^$", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    )
