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
import uuid
import json
from unittest.mock import MagicMock, patch

import pytest

from bk_plugin_framework.kit import State
from bk_plugin_framework.utils import local
from bk_plugin_framework.runtime.callback.celery import tasks


@pytest.fixture
def trace_id():
    return uuid.uuid4().hex


@pytest.fixture
def callback_id():
    return uuid.uuid4().hex


@pytest.fixture
def callback_data():
    return json.dumps({"result": "True", "data": {}})


class MockScheduleLock(object):
    def __init__(self, trace_id: str, locked: bool):
        self.trace_id = trace_id
        self.locked = locked

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def mock_schedule_lock(trace_id):
    return MockScheduleLock(trace_id, True)


def mock_schedule_lock_fail(trace_id):
    return MockScheduleLock(trace_id, False)


class TestCallbackTask:
    def test_callback_get_lock_fail(self, trace_id, callback_id, callback_data):
        task = MagicMock()
        task.apply_async = MagicMock()
        random = MagicMock()
        random.randint = MagicMock(return_value=2)

        class CurrentApp(object):
            def __init__(self):
                self.tasks = {"bk_plugin_framework.runtime.callback.celery.tasks.callback": task}

        current_app = CurrentApp()
        with patch("bk_plugin_framework.runtime.callback.celery.tasks.get_schedule_lock", mock_schedule_lock_fail):
            with patch("bk_plugin_framework.runtime.callback.celery.tasks.current_app", current_app):
                with patch("bk_plugin_framework.runtime.callback.celery.tasks.random", random):
                    tasks.callback(trace_id, callback_id, callback_data)

        current_app.tasks[
            "bk_plugin_framework.runtime.callback.celery.tasks.callback"
        ].apply_async.assert_called_once_with(
            **{
                "kwargs": {"trace_id": trace_id, "callback_id": callback_id, "callback_data": callback_data},
                "countdown": 2,
                "queue": "plugin_callback",
            }
        )

    def test_callback_state_not_callback(self, trace_id, callback_id, callback_data):
        schedule_obj = MagicMock(state=4)
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        with patch("bk_plugin_framework.runtime.callback.celery.tasks.get_schedule_lock", mock_schedule_lock):
            with patch("bk_plugin_framework.runtime.callback.celery.tasks.Schedule", Schedule):
                tasks.callback(trace_id, callback_id, callback_data)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)

    def test_callback__get_schedule_obj_err(self, trace_id, callback_id, callback_data):
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(side_effect=Exception)
        with patch("bk_plugin_framework.runtime.callback.celery.tasks.get_schedule_lock", mock_schedule_lock):
            with patch("bk_plugin_framework.runtime.callback.celery.tasks.Schedule", Schedule):
                tasks.callback(trace_id, callback_id, callback_data)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter(trace_id=trace_id).update.assert_called_once_with(state=State.FAIL.value)

    def test_callback__plugin_version_missing(self, trace_id, callback_id, callback_data):
        schedule_obj = MagicMock(state=3)
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        VersionHub = MagicMock()
        VersionHub.all_plugins().get = MagicMock(return_value=None)
        with patch("bk_plugin_framework.runtime.callback.celery.tasks.get_schedule_lock", mock_schedule_lock):
            with patch("bk_plugin_framework.runtime.callback.celery.tasks.Schedule", Schedule):
                with patch("bk_plugin_framework.runtime.callback.celery.tasks.VersionHub", VersionHub):
                    tasks.callback(trace_id, callback_id, callback_data)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        VersionHub.all_plugins().get.assert_called_once_with(schedule_obj.plugin_version)
        Schedule.objects.filter.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter(trace_id=trace_id).update.assert_called_once_with(state=State.FAIL.value)

    def test_callback__execute_err(self, trace_id, callback_id, callback_data):
        schedule_obj = MagicMock(state=3)
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        VersionHub = MagicMock()
        executor = MagicMock()
        executor.schedule = MagicMock(side_effect=Exception)
        BKPluginExecutor = MagicMock(return_value=executor)
        with patch("bk_plugin_framework.runtime.callback.celery.tasks.get_schedule_lock", mock_schedule_lock):
            with patch("bk_plugin_framework.runtime.callback.celery.tasks.Schedule", Schedule):
                with patch("bk_plugin_framework.runtime.callback.celery.tasks.VersionHub", VersionHub):
                    with patch("bk_plugin_framework.runtime.callback.celery.tasks.BKPluginExecutor", BKPluginExecutor):
                        tasks.callback(trace_id, callback_id, callback_data)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        VersionHub.all_plugins().get.assert_called_once_with(schedule_obj.plugin_version)
        BKPluginExecutor.assert_called_once_with(trace_id=trace_id)
        executor.schedule.assert_called_once_with(
            plugin_cls=VersionHub.all_plugins().get(schedule_obj.plugin_version),
            schedule=schedule_obj,
            callback_info={"callback_id": callback_id, "callback_data": json.loads(callback_data)},
        )
        Schedule.objects.filter.assert_called_once_with(trace_id=trace_id)
        Schedule.objects.filter(trace_id=trace_id).update.assert_called_once_with(state=State.FAIL.value)

    def test_callback__execute_success(self, trace_id, callback_id, callback_data):
        schedule_obj = MagicMock(state=3)
        Schedule = MagicMock()
        Schedule.objects.get = MagicMock(return_value=schedule_obj)
        VersionHub = MagicMock()
        executor = MagicMock()
        BKPluginExecutor = MagicMock(return_value=executor)
        with patch("bk_plugin_framework.runtime.callback.celery.tasks.get_schedule_lock", mock_schedule_lock):
            with patch("bk_plugin_framework.runtime.callback.celery.tasks.Schedule", Schedule):
                with patch("bk_plugin_framework.runtime.callback.celery.tasks.VersionHub", VersionHub):
                    with patch("bk_plugin_framework.runtime.callback.celery.tasks.BKPluginExecutor", BKPluginExecutor):
                        tasks.callback(trace_id, callback_id, callback_data)

        assert local.get_trace_id() == trace_id

        Schedule.objects.get.assert_called_once_with(trace_id=trace_id)
        VersionHub.all_plugins().get.assert_called_once_with(schedule_obj.plugin_version)
        BKPluginExecutor.assert_called_once_with(trace_id=trace_id)
        executor.schedule.assert_called_once_with(
            plugin_cls=VersionHub.all_plugins().get(schedule_obj.plugin_version),
            schedule=schedule_obj,
            callback_info={"callback_id": callback_id, "callback_data": json.loads(callback_data)},
        )
        Schedule.objects.filter.assert_not_called()
