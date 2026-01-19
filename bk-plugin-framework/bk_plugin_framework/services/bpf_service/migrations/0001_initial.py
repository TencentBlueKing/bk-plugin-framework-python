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
            name="APIGatewaySyncState",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "api_hash",
                    models.CharField(
                        default="",
                        max_length=64,
                        verbose_name="接口定义哈希值",
                    ),
                ),
                (
                    "last_sync_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="上次同步时间",
                    ),
                ),
                (
                    "sync_success",
                    models.BooleanField(
                        default=False,
                        verbose_name="同步是否成功",
                    ),
                ),
            ],
            options={
                "verbose_name": "API网关同步状态",
                "verbose_name_plural": "API网关同步状态",
                "db_table": "bpf_apigateway_sync_state",
            },
        ),
    ]
