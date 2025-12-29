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
from bk_plugin_framework.kit import State
from bk_plugin_framework.runtime.schedule.celery import tasks
from bk_plugin_framework.utils import local


@pytest.fixture
def trace_id():
    return uuid.uuid4().hex


@pytest.fixture
def schedule_id():
    return 1


class TestScheduleTask:
    def test_schedule__get_schedule_obj_err(self, trace_id, schedule_id):
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(side_effect=Exception)

        with patch("bk_plugin_framework.runtime.schedule.celery.tasks.Schedule", Schedule):
            tasks.schedule(trace_id)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter(trace_id=trace_id).update.assert_called_once_with(state=State.FAIL.value)

    def test_schedule__plugin_version_missing(self, trace_id, schedule_id):
        schedule_obj = MagicMock()
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        VersionHub = MagicMock()
        VersionHub.all_plugins().get = MagicMock(return_value=None)

        with patch("bk_plugin_framework.runtime.schedule.celery.tasks.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.schedule.celery.tasks.VersionHub", VersionHub):
                tasks.schedule(trace_id)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        VersionHub.all_plugins().get.assert_called_once_with(schedule_obj.plugin_version)
        Schedule.objects.filter.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter(trace_id=trace_id).update.assert_called_once_with(state=State.FAIL.value)

    def test_schedule__execute_err(self, trace_id, schedule_id):
        schedule_obj = MagicMock()
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        VersionHub = MagicMock()
        executor = MagicMock()
        executor.schedule = MagicMock(side_effect=Exception)
        BKPluginExecutor = MagicMock(return_value=executor)

        with patch("bk_plugin_framework.runtime.schedule.celery.tasks.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.schedule.celery.tasks.VersionHub", VersionHub):
                with patch("bk_plugin_framework.runtime.schedule.celery.tasks.BKPluginExecutor", BKPluginExecutor):
                    tasks.schedule(trace_id)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        VersionHub.all_plugins().get.assert_called_once_with(schedule_obj.plugin_version)
        BKPluginExecutor.assert_called_once_with(trace_id=trace_id)
        executor.schedule.assert_called_once_with(
            plugin_cls=VersionHub.all_plugins().get(schedule_obj.plugin_version), schedule=schedule_obj
        )
        Schedule.objects.filter.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter(trace_id=trace_id).update.assert_called_once_with(state=State.FAIL.value)

    def test_schedule__execute_success(self, trace_id, schedule_id):
        schedule_obj = MagicMock()
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        VersionHub = MagicMock()
        executor = MagicMock()
        BKPluginExecutor = MagicMock(return_value=executor)

        with patch("bk_plugin_framework.runtime.schedule.celery.tasks.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.schedule.celery.tasks.VersionHub", VersionHub):
                with patch("bk_plugin_framework.runtime.schedule.celery.tasks.BKPluginExecutor", BKPluginExecutor):
                    tasks.schedule(trace_id)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        VersionHub.all_plugins().get.assert_called_once_with(schedule_obj.plugin_version)
        BKPluginExecutor.assert_called_once_with(trace_id=trace_id)
        executor.schedule.assert_called_once_with(
            plugin_cls=VersionHub.all_plugins().get(schedule_obj.plugin_version), schedule=schedule_obj
        )
        Schedule.objects.filter.assert_not_called()
