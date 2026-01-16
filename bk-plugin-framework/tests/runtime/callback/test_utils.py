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

import uuid

import pytest

from bk_plugin_framework.runtime.callback.api import CallbackPreparation, parse_callback_token, prepare_callback


@pytest.fixture
def trace_id():
    return uuid.uuid4().hex


class TestCallbackUtils:
    def test_pre_callback(self, trace_id):
        callback = prepare_callback(trace_id)

        assert isinstance(callback, CallbackPreparation)
        assert len(callback.id) == 32

    def test_parse_callback_token_success(self, trace_id):
        callback = prepare_callback(trace_id)

        parse_result = parse_callback_token(callback.url.split("/")[-2])

        assert parse_result == {"result": True, "data": {"callback_id": callback.id, "trace_id": trace_id}}

    def test_parse_callback_token_invalid(self):
        parse_result = parse_callback_token("aaa")

        assert parse_result == {"result": False, "message": "invalid token aaa"}
