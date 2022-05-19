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
import pytest

from unittest.mock import MagicMock, patch

from bk_plugin_framework.kit import (
    Plugin,
    InputsModel,
    OutputsModel,
    ContextRequire,
    Callback,
    Context,
    State,
)
from bk_plugin_framework.runtime.callback.api import CallbackPreparation


@patch("bk_plugin_framework.hub.load_form_module_path", MagicMock(return_value="tests"))
@pytest.fixture
def my_plugin_cls():
    class MyPlugin(Plugin):
        class Meta:
            version = "1.0.0"

        class Inputs(InputsModel):
            a: int

        class ContextInputs(ContextRequire):
            b: str

    return MyPlugin


@patch("bk_plugin_framework.hub.load_form_module_path", MagicMock(return_value="tests"))
@pytest.fixture
def my_plugin_cls_v101():
    class MyPlugin(Plugin):
        class Meta:
            version = "1.0.1"

        class Inputs(InputsModel):
            a: int

        class Outputs(OutputsModel):
            pass

        class ContextInputs(ContextRequire):
            b: str

    return MyPlugin


@pytest.fixture
def my_plugin(my_plugin_cls):
    return my_plugin_cls()


class TestContext:
    def test_schedule_context(self):
        class ContextInputs(ContextRequire):
            a: int

        context = Context(
            trace_id="", data=ContextInputs(a=1), state=State.EMPTY, invoke_count=1, storage={"b": 2}, outputs={"c": 3}
        )

        assert context.schedule_context == {
            "storage": context.storage,
            "outputs": context.outputs,
            "data": context.data.dict(),
        }

    def test_callback_context(self):
        class ContextInputs(ContextRequire):
            a: int

        callback = Callback(callback_id="callback_id", callback_data={"result": True, "data": {}})
        context = Context(
            trace_id="",
            data=ContextInputs(a=1),
            state=State.EMPTY,
            invoke_count=1,
            storage={"b": 2},
            outputs={"c": 3},
            callback=callback,
        )

        assert context.callback.id == "callback_id"
        assert context.callback.data == {"result": True, "data": {}}


class TestPlugin:
    def test_execute(self, my_plugin):

        try:
            my_plugin.execute(MagicMock(), MagicMock())
        except NotImplementedError:
            pass
        else:
            assert False

    def test_wait_poll(self, my_plugin):

        assert my_plugin.poll_interval == -1
        my_plugin.wait_poll(3)
        assert my_plugin.poll_interval == 3
        my_plugin.wait_poll(0)
        assert my_plugin.poll_interval == 0
        my_plugin.wait_poll(-1)
        assert my_plugin.poll_interval == 0

    def test_is_wating_poll(self, my_plugin):

        assert my_plugin.is_wating_poll is False
        my_plugin.wait_poll(3)
        assert my_plugin.is_wating_poll is True

    def test_wait_callback(self, my_plugin):

        assert my_plugin.is_wating_poll is False
        assert my_plugin.is_waiting_callback is False
        my_plugin.wait_poll(3)
        assert my_plugin.is_waiting_callback is False
        assert my_plugin.is_wating_poll is True
        my_plugin.wait_callback()
        assert my_plugin.is_waiting_callback is True
        assert my_plugin.is_wating_poll is False

    def test_pre_callback(self, my_plugin):
        class ContextInputs(ContextRequire):
            a: int

        context = Context(
            trace_id="", data=ContextInputs(a=1), state=State.EMPTY, invoke_count=1, storage={"b": 2}, outputs={"c": 3}
        )
        prepare_callback = my_plugin.prepare_callback(context)

        assert isinstance(prepare_callback, CallbackPreparation)
        assert len(prepare_callback.id) == 32

    def test_dict(self, my_plugin_cls):
        assert my_plugin_cls.dict() == {
            "desc": "",
            "version": my_plugin_cls.Meta.version,
            "inputs": {
                "type": my_plugin_cls.Inputs.schema()["type"],
                "properties": my_plugin_cls.Inputs.schema()["properties"],
                "required": my_plugin_cls.Inputs.schema()["required"],
                "definitions": my_plugin_cls.Inputs.schema().get("definitions", {}),
            },
            "outputs": my_plugin_cls._EMPTY_SCHEMA,
            "context_inputs": {
                "type": my_plugin_cls.ContextInputs.schema()["type"],
                "properties": my_plugin_cls.ContextInputs.schema()["properties"],
                "required": my_plugin_cls.ContextInputs.schema()["required"],
                "definitions": my_plugin_cls.ContextInputs.schema().get("definitions", {}),
            },
            "forms": {
                "renderform": my_plugin_cls.renderform,
            },
        }

    def test_dict_pass_outputs_model(self, my_plugin_cls_v101):
        my_plugin_cls = my_plugin_cls_v101
        assert my_plugin_cls.dict() == {
            "desc": "",
            "version": my_plugin_cls.Meta.version,
            "inputs": {
                "type": my_plugin_cls.Inputs.schema()["type"],
                "properties": my_plugin_cls.Inputs.schema()["properties"],
                "required": my_plugin_cls.Inputs.schema()["required"],
                "definitions": my_plugin_cls.Inputs.schema().get("definitions", {}),
            },
            "outputs": my_plugin_cls._EMPTY_SCHEMA,
            "context_inputs": {
                "type": my_plugin_cls.ContextInputs.schema()["type"],
                "properties": my_plugin_cls.ContextInputs.schema()["properties"],
                "required": my_plugin_cls.ContextInputs.schema()["required"],
                "definitions": my_plugin_cls.ContextInputs.schema().get("definitions", {}),
            },
            "forms": {
                "renderform": my_plugin_cls.renderform,
            },
        }
