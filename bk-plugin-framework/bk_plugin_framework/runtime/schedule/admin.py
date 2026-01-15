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


from django.contrib import admin

from bk_plugin_framework.runtime.schedule import models


@admin.register(models.Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    search_fields = ["trace_id__exact"]
    list_display = ["trace_id", "plugin_version", "state", "created_at", "finish_at"]
