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
from unittest.mock import MagicMock

from bk_plugin_framework.utils import local
from bk_plugin_framework.utils.log import TraceIDInjectFilter


class TestTraceIDInjectFilter:
    def test_filter(self):
        # prepare
        trace_id = "trace_id_token"
        local.set_trace_id(trace_id)
        record = MagicMock()
        _filter = TraceIDInjectFilter()

        # test
        _filter.filter(record)
        assert record.trace_id == trace_id
