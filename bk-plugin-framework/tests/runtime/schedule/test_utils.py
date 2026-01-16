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
from unittest.mock import MagicMock, patch

import pytest

from bk_plugin_framework.runtime.schedule.utils import get_schedule_lock


@pytest.fixture
def trace_id():
    return uuid.uuid4().hex


class TestScheduleUtils:
    def test_schedule_lock_success(self, trace_id):
        Schedule = MagicMock()
        Schedule.objects.apply_schedule_lock = MagicMock(return_value=True)
        Schedule.objects.release_schedule_lock = MagicMock()
        with patch("bk_plugin_framework.runtime.schedule.utils.Schedule", Schedule):
            with get_schedule_lock(trace_id) as lock:
                assert lock.locked
                Schedule.objects.apply_schedule_lock.assert_called_once_with(trace_id)

            Schedule.objects.release_schedule_lock.assert_called_once_with(trace_id)

    def test_schedule_lock_fail(self, trace_id):
        Schedule = MagicMock()
        Schedule.objects.apply_schedule_lock = MagicMock(return_value=False)
        Schedule.objects.release_schedule_lock = MagicMock()
        with patch("bk_plugin_framework.runtime.schedule.utils.Schedule", Schedule):
            with get_schedule_lock(trace_id) as lock:
                assert not lock.locked
                Schedule.objects.apply_schedule_lock.assert_called_once_with(trace_id)

            Schedule.objects.release_schedule_lock.assert_not_called()
