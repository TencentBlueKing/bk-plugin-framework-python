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


from django.db import models


class LogEntryManager(models.Manager):
    def get_plain_log(self, trace_id: str) -> str:
        return "\n".join([le.message for le in self.order_by("id").filter(trace_id=trace_id).only("message")])


class LogEntry(models.Model):
    id = models.BigAutoField("ID", primary_key=True)
    trace_id = models.CharField("trace id", max_length=33, db_index=True)
    logger_name = models.CharField("logger name", max_length=128)
    level_name = models.CharField("log level", max_length=32)
    message = models.TextField("log content", null=True)
    logged_at = models.DateTimeField("log at", auto_now_add=True, db_index=True)

    objects = LogEntryManager()
