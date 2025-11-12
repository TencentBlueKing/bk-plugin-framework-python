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
import json
import pytest

from unittest.mock import MagicMock, patch

from bk_plugin_framework.kit import (
    Plugin,
    InputsModel,
    ContextRequire,
    Context,
    State,
    Credential,
    CredentialModel,
)
from bk_plugin_framework.runtime.executor import BKPluginExecutor


@pytest.fixture
def executor():
    return BKPluginExecutor("")


@pytest.fixture
def executor_1():
    executor = BKPluginExecutor("")
    executor._set_schedule_state = MagicMock()
    return executor


@pytest.fixture
def executor_2():
    executor = BKPluginExecutor("")
    executor._set_schedule_state = MagicMock()
    executor._dump_schedule_data = MagicMock(side_effect=Exception)
    return executor


@pytest.fixture
def plugin_cls():
    class MyPlugin(Plugin):
        class Meta:
            version = "1.0.0"

        class Inputs(InputsModel):
            success: bool
            raise_unexpected_err: bool = False
            poll: bool = False
            callback: bool = False

        class ContextInputs(ContextRequire):
            b: str

        def execute(self, inputs: InputsModel, context: Context):
            if inputs.raise_unexpected_err:
                raise Exception("fail")

            if inputs.success:
                if inputs.poll:
                    self.wait_poll(1)
                if inputs.callback:
                    self.wait_callback()
                return
            else:
                raise self.Error("fail")

    return MyPlugin


@pytest.fixture
def empty_plugin_cls():
    class MyPlugin(Plugin):
        class Meta:
            version = "1.0.1"

        def execute(self, inputs: InputsModel, context: Context):
            return

    return MyPlugin


class TestBKPluginExecutor:
    def test__dump_schedule_data(self, executor):
        inputs = {"a": 1}
        outputs = {"b": 2}
        context = {"c": 3}
        kwargs = {"inputs": inputs, "context": context, "outputs": outputs}

        assert json.dumps(kwargs) == executor._dump_schedule_data(**kwargs)

    def test__load_schedule_data(self, executor):
        schedule = MagicMock()
        schedule.data = '{"a": 1}'

        assert executor._load_schedule_data(schedule) == {"a": 1}

    @pytest.mark.parametrize("state", [State.POLL, State.CALLBACK])
    def test__set_schedule_state_not_finish_state(self, executor, state):
        schedule_obj = MagicMock()
        Schedule = MagicMock()

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            executor._set_schedule_state(trace_id=schedule_obj.trace_id, state=state)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule_obj.trace_id)
        Schedule.objects.filter(trace_id=schedule_obj.trace_id).update.assert_called_once_with(state=state.value)

    @pytest.mark.parametrize("state", [State.FAIL, State.SUCCESS])
    def test__set_schedule_state_finish_state(self, executor, state):
        schedule_obj = MagicMock()
        Schedule = MagicMock()
        now = MagicMock(return_value="now")

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.now", now):
                executor._set_schedule_state(trace_id=schedule_obj.trace_id, state=state)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule_obj.trace_id)
        Schedule.objects.filter(trace_id=schedule_obj.trace_id).update.assert_called_once_with(
            state=state.value, finish_at="now"
        )

    def test_execute__inputs_validate_err(self, executor, plugin_cls):
        result = executor.execute(plugin_cls, {}, {})

        assert result.state is State.FAIL
        assert result.outputs is None
        assert "inputs validation error" in result.err

    def test_execute__context_inputs_validate_err(self, executor, plugin_cls):
        result = executor.execute(plugin_cls, {"success": True}, {})

        assert result.state is State.FAIL
        assert result.outputs is None
        assert "context validation error" in result.err

    def test_execute__plugin_execute_raise_expected_err(self, executor, plugin_cls):
        result = executor.execute(plugin_cls, {"success": False}, {"b": "1"})

        assert result.state is State.FAIL
        assert result.outputs is None
        assert "plugin execute failed" in result.err

    def test_execute__plugin_execute_raise_unexpected_err(self, executor, plugin_cls):
        result = executor.execute(plugin_cls, {"success": True, "raise_unexpected_err": True}, {"b": "1"})

        assert result.state is State.FAIL
        assert result.outputs is None
        assert "plugin execute raise unexpected error" in result.err

    def test_execute__success(self, executor, plugin_cls):
        result = executor.execute(plugin_cls, {"success": True}, {"b": "1"})

        assert result.state is State.SUCCESS
        assert result.outputs == {}
        assert result.err is None

    def test_execute__waiting_poll(self, executor, plugin_cls):
        schedule_obj = MagicMock()
        Schedule = MagicMock()
        Schedule.objects.create = MagicMock(return_value=schedule_obj)
        current_app = MagicMock()

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.current_app", current_app):
                result = executor.execute(plugin_cls, {"success": True, "poll": True}, {"b": "1"})

        assert result.state is State.POLL
        assert result.outputs == {}
        assert result.err is None

        Schedule.objects.create.assert_called_once_with(
            trace_id=executor.trace_id,
            state=State.POLL.value,
            plugin_version=plugin_cls.Meta.version,
            data='{"inputs": {"success": true, "poll": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}',  # noqa
        )
        current_app.tasks[executor.SCHEDULE_TASK_NAME].apply_async.assert_called_once_with(
            kwargs={"trace_id": executor.trace_id},
            countdown=1,
            queue="plugin_schedule",
        )

    def test_schedule__load_schedule_data_err(self, executor_1, plugin_cls):
        schedule = MagicMock()
        schedule.data = "invalid data"

        executor_1.schedule(plugin_cls, schedule)

        executor_1._set_schedule_state.assert_called_once_with(trace_id=schedule.trace_id, state=State.FAIL)

    def test_schedule__plugin_inputs_validation_err(self, executor_1, plugin_cls):
        schedule = MagicMock()
        schedule.data = (
            '{"inputs": {}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa
        )

        executor_1.schedule(plugin_cls, schedule)

        executor_1._set_schedule_state.assert_called_once_with(trace_id=schedule.trace_id, state=State.FAIL)

    def test_schedule__plugin_context_validation_err(self, executor_1, plugin_cls):
        schedule = MagicMock()
        schedule.data = '{"inputs": {"success": true, "poll": true}, "context": {"storage": {}, "outputs": {}, "data": {}, "credentials": {}}, "outputs": {}}'  # noqa

        executor_1.schedule(plugin_cls, schedule)

        executor_1._set_schedule_state.assert_called_once_with(trace_id=schedule.trace_id, state=State.FAIL)

    def test_schedule__plugin_execute_raise_expected_err(self, executor, plugin_cls):
        schedule = MagicMock()
        schedule.invoke_count = 1
        schedule.data = '{"inputs": {"success": false, "poll": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa
        Schedule = MagicMock()
        now = MagicMock(return_value="now")

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.now", now):
                executor.schedule(plugin_cls, schedule)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule.trace_id)
        # The data will be updated with credentials included
        update_call = Schedule.objects.filter(trace_id=schedule.trace_id).update.call_args
        assert update_call is not None
        assert update_call.kwargs["state"] == State.FAIL.value
        assert update_call.kwargs["invoke_count"] == 2
        assert update_call.kwargs["finish_at"] == "now"
        assert update_call.kwargs["err"] == "plugin schedule failed: fail"
        # Verify credentials is included in the data
        updated_data = json.loads(update_call.kwargs["data"])
        assert "credentials" in updated_data["context"]

    def test_schedule__plugin_execute_raise_unexpected_err(self, executor, plugin_cls):
        schedule = MagicMock()
        schedule.invoke_count = 1
        schedule.data = '{"inputs": {"success": true, "poll": true, "raise_unexpected_err": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa
        Schedule = MagicMock()
        now = MagicMock(return_value="now")

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.now", now):
                executor.schedule(plugin_cls, schedule)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule.trace_id)
        Schedule.objects.filter(trace_id=schedule.trace_id).update.assert_called_once_with(
            state=State.FAIL.value, invoke_count=2, finish_at="now", err="plugin schedule failed: fail"
        )

    def test_schedule__plugin_execute_waiting_poll(self, executor, plugin_cls):
        schedule = MagicMock()
        schedule.invoke_count = 1
        schedule.data = '{"inputs": {"success": true, "poll": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa
        Schedule = MagicMock()
        current_app = MagicMock()

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.current_app", current_app):
                executor.schedule(plugin_cls, schedule)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule.trace_id)
        # The data will be updated with credentials included
        update_call = Schedule.objects.filter(trace_id=schedule.trace_id).update.call_args
        assert update_call is not None
        assert update_call.kwargs["state"] == State.POLL.value
        assert update_call.kwargs["invoke_count"] == 2
        updated_data = json.loads(update_call.kwargs["data"])
        assert "credentials" in updated_data["context"]
        current_app.tasks[executor.SCHEDULE_TASK_NAME].apply_async.assert_called_once_with(
            kwargs={"trace_id": executor.trace_id},
            countdown=1,
            queue="plugin_schedule",
        )

    def test_schedule__plugin_execute_waiting_callback(self, executor, plugin_cls):
        schedule = MagicMock()
        schedule.invoke_count = 1
        schedule.state = State.CALLBACK.value
        schedule.data = '{"inputs": {"success": true, "poll": true, "callback": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa
        Schedule = MagicMock()
        current_app = MagicMock()
        callback_info = {"callback_id": "callback_id", "callback_data": {"result": True, "data": {}}}
        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.current_app", current_app):
                executor.schedule(plugin_cls, schedule, callback_info)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule.trace_id)
        # The data will be updated with credentials included
        update_call = Schedule.objects.filter(trace_id=schedule.trace_id).update.call_args
        assert update_call is not None
        assert update_call.kwargs["state"] == State.CALLBACK.value
        assert update_call.kwargs["invoke_count"] == 2
        updated_data = json.loads(update_call.kwargs["data"])
        assert "credentials" in updated_data["context"]

    def test_schedule__plugin_execute_success(self, executor, plugin_cls):
        schedule = MagicMock()
        schedule.invoke_count = 1
        schedule.data = '{"inputs": {"success": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa
        Schedule = MagicMock()
        now = MagicMock(return_value="now")

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.now", now):
                executor.schedule(plugin_cls, schedule)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule.trace_id)
        # The data will be updated with credentials included
        update_call = Schedule.objects.filter(trace_id=schedule.trace_id).update.call_args
        assert update_call is not None
        assert update_call.kwargs["state"] == State.SUCCESS.value
        assert update_call.kwargs["invoke_count"] == 2
        assert update_call.kwargs["finish_at"] == "now"
        updated_data = json.loads(update_call.kwargs["data"])
        assert "credentials" in updated_data["context"]

    def test_schedule__plugin_execute_success_dump_data_err(self, executor_2, plugin_cls):
        schedule = MagicMock()
        schedule.data = '{"inputs": {"success": true}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'  # noqa

        executor_2.schedule(plugin_cls, schedule)

        executor_2._set_schedule_state.assert_called_once_with(trace_id=schedule.trace_id, state=State.FAIL)

    def test_execute__plugin_inputs_and_context_not_define(self, executor, empty_plugin_cls):
        result = executor.execute(empty_plugin_cls, {"success": True}, {"b": "1"})

        assert result.state is State.SUCCESS
        assert result.outputs == {}
        assert result.err is None

    def test_schedule__plugin_inputs_and_context_not_define(self, executor, empty_plugin_cls):
        schedule = MagicMock()
        schedule.invoke_count = 1
        schedule.data = '{"inputs": {}, "context": {"storage": {}, "outputs": {}, "data": {"b": "1"}, "credentials": {}}, "outputs": {}}'
        Schedule = MagicMock()
        now = MagicMock(return_value="now")

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.now", now):
                executor.schedule(empty_plugin_cls, schedule)

        Schedule.objects.filter.assert_called_once_with(trace_id=schedule.trace_id)
        # The data will be updated with credentials included
        update_call = Schedule.objects.filter(trace_id=schedule.trace_id).update.call_args
        assert update_call is not None
        assert update_call.kwargs["state"] == State.SUCCESS.value
        assert update_call.kwargs["invoke_count"] == 2
        assert update_call.kwargs["finish_at"] == "now"
        updated_data = json.loads(update_call.kwargs["data"])
        assert "credentials" in updated_data["context"]
        assert updated_data["context"]["data"] == {}

    @patch("bk_plugin_framework.hub.load_form_module_path", MagicMock(return_value="tests"))
    def test_execute__with_credentials(self, executor):
        class PluginWithCredentials(Plugin):
            class Meta:
                version = "1.0.5"

            class Inputs(InputsModel):
                success: bool

            class ContextInputs(ContextRequire):
                b: str

            class Credentials(CredentialModel):
                api_key = Credential(key="api_key", name="API Key")

            def execute(self, inputs: InputsModel, context: Context):
                assert context.credentials.get("api_key") == "test_key"
                if inputs.success:
                    return
                else:
                    raise self.Error("fail")

        credentials = {"api_key": "test_key"}
        result = executor.execute(
            PluginWithCredentials, {"success": True}, {"b": "1"}, credentials=credentials
        )

        assert result.state is State.SUCCESS
        assert result.outputs == {}
        assert result.err is None

    @patch("bk_plugin_framework.hub.load_form_module_path", MagicMock(return_value="tests"))
    def test_execute__credentials_passed_to_context(self, executor):
        class PluginWithCredentials(Plugin):
            class Meta:
                version = "1.0.6"

            class Inputs(InputsModel):
                success: bool

            class ContextInputs(ContextRequire):
                b: str

            class Credentials(CredentialModel):
                api_key = Credential(key="api_key")
                api_secret = Credential(key="api_secret")

            def execute(self, inputs: InputsModel, context: Context):
                assert "api_key" in context.credentials
                assert "api_secret" in context.credentials
                assert context.credentials["api_key"] == "key_value"
                assert context.credentials["api_secret"] == "secret_value"
                if inputs.success:
                    return
                else:
                    raise self.Error("fail")

        credentials = {"api_key": "key_value", "api_secret": "secret_value"}
        result = executor.execute(
            PluginWithCredentials, {"success": True}, {"b": "1"}, credentials=credentials
        )

        assert result.state is State.SUCCESS

    @patch("bk_plugin_framework.hub.load_form_module_path", MagicMock(return_value="tests"))
    def test_schedule__credentials_persisted(self, executor):
        class PluginWithCredentials(Plugin):
            class Meta:
                version = "1.0.7"

            class Inputs(InputsModel):
                success: bool
                poll: bool = False

            class ContextInputs(ContextRequire):
                b: str

            class Credentials(CredentialModel):
                api_key = Credential(key="api_key")

            def execute(self, inputs: InputsModel, context: Context):
                assert context.credentials.get("api_key") == "persisted_key"
                if inputs.success:
                    if inputs.poll:
                        self.wait_poll(1)
                    return
                else:
                    raise self.Error("fail")

        credentials = {"api_key": "persisted_key"}
        schedule_obj = MagicMock()
        Schedule = MagicMock()
        Schedule.objects.create = MagicMock(return_value=schedule_obj)
        current_app = MagicMock()

        with patch("bk_plugin_framework.runtime.executor.Schedule", Schedule):
            with patch("bk_plugin_framework.runtime.executor.current_app", current_app):
                result = executor.execute(
                    PluginWithCredentials, {"success": True, "poll": True}, {"b": "1"}, credentials=credentials
                )

        assert result.state is State.POLL
        # Verify credentials are included in schedule data
        create_call_args = Schedule.objects.create.call_args
        assert create_call_args is not None
        schedule_data = json.loads(create_call_args.kwargs["data"])
        assert "credentials" in schedule_data["context"]
        assert schedule_data["context"]["credentials"]["api_key"] == "persisted_key"
