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

import logging
from logging import LogRecord

from django.core.exceptions import AppRegistryNotReady

from bk_plugin_framework.utils import local


class TraceContextLogHandler(logging.Handler):
    def emit(self, record: LogRecord):
        try:
            from bk_plugin_framework.runtime.loghub.models import LogEntry
        except AppRegistryNotReady:
            return

        trace_id = local.get_trace_id()
        if trace_id is None:
            return

        LogEntry.objects.create(
            trace_id=trace_id, logger_name=record.name, level_name=record.levelname, message=self.format(record)
        )
