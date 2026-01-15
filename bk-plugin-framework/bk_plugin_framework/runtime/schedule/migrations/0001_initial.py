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


from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Schedule",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False, verbose_name="ID")),
                ("trace_id", models.CharField(db_index=True, max_length=33, verbose_name="trace id")),
                ("plugin_version", models.CharField(max_length=128, verbose_name="plugin version")),
                ("state", models.IntegerField(verbose_name="execution state")),
                ("invoke_count", models.IntegerField(default=1, verbose_name="invoke count")),
                ("data", models.TextField(verbose_name="context and inputs")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="create time")),
            ],
        ),
    ]
