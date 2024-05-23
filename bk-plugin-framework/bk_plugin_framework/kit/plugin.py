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

import re
import typing
import inspect

try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel

from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.constants import State
from bk_plugin_framework.runtime.callback.api import prepare_callback, CallbackPreparation

VALID_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9][a-z0-9]*$")


class FormModel:
    @classmethod
    def fields(cls):
        attributes = inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        return [attr[0] for attr in attributes if not attr[0].startswith("_")]


class InputsModel(BaseModel):
    pass


class OutputsModel(BaseModel):
    pass


class PluginCallbackModel(BaseModel):
    url: str
    data: dict


class ContextRequire(BaseModel):
    pass


class Callback(object):
    def __init__(self, callback_id: str = "", callback_data: dict = {}):
        self.id = callback_id
        self.data = callback_data


class Context:
    def __init__(
        self,
        trace_id: str,
        data: ContextRequire,
        state: State,
        invoke_count: int,
        callback: Callback = None,
        outputs: typing.Optional[dict] = None,
        storage: typing.Optional[dict] = None,
    ):
        self.trace_id = trace_id
        self.data = data
        self.state = state
        self.invoke_count = invoke_count
        self.callback = callback
        self.storage = storage or {}
        self.outputs = outputs or {}

    @property
    def schedule_context(self) -> dict:
        return {
            "storage": self.storage,
            "outputs": self.outputs,
            "data": self.data.dict(),
        }

    @property
    def plugin_callback_info(self) -> typing.Optional[PluginCallbackModel]:
        return getattr(self.data, "plugin_callback_info", None)


class PluginMeta(type):
    def __new__(cls, name, bases, dct):
        # ensure initialization is only performed for subclasses of Plugin
        parents = [b for b in bases if isinstance(b, PluginMeta)]
        if not parents:
            return super().__new__(cls, name, bases, dct)

        new_cls = super().__new__(cls, name, bases, dct)

        # meta validation
        meta_obj = getattr(new_cls, "Meta", None)
        if not meta_obj:
            raise RuntimeError("plugin deinition error, can not retrive Meta attribute in {}".format(new_cls))

        # meta.version validation
        version = getattr(meta_obj, "version", None)
        if not version:
            raise RuntimeError("plugin deinition error, can not retrive version field in {}.Meta".format(new_cls))

        if not isinstance(version, str):
            raise TypeError("plugin deinition error, version field is not a string in {}.Meta".format(new_cls))

        if not VALID_VERSION_PATTERN.match(version):
            raise ValueError(
                "plugin deinition error, version({}) in {}.Meta is not a valid version".format(version, new_cls)
            )

        if len(version) > 128:
            raise ValueError("plugin deinition error, version({}) length exceed 128".format(version))

        # meta.desc validation
        desc = getattr(meta_obj, "desc", None)
        if desc is not None and not isinstance(desc, str):
            raise TypeError("plugin deinition error, desc field is not a string in {}.Meta".format(new_cls))

        # inputs check
        inputs_cls = getattr(new_cls, "Inputs", None)
        if inputs_cls and not issubclass(inputs_cls, InputsModel):
            raise TypeError("plugin deinition error, {}'s Inputs is not subclass of {}".format(new_cls, InputsModel))

        # outputs check
        outputs_cls = getattr(new_cls, "Outputs", None)
        if outputs_cls and not issubclass(outputs_cls, OutputsModel):
            raise TypeError("plugin deinition error, {}'s Outputs is not subclass of {}".format(new_cls, OutputsModel))

        # context check
        context_cls = getattr(new_cls, "ContextInputs", None)
        if context_cls and not issubclass(context_cls, ContextRequire):
            raise TypeError(
                "plugin deinition error, {}'s ContextInputs is not subclass of {}".format(new_cls, ContextRequire)
            )

        # inputs form check
        inputs_form_cls = getattr(new_cls, "InputsForm", None)
        if inputs_form_cls and not issubclass(inputs_form_cls, FormModel):
            raise TypeError("plugin deinition error, {}'s InputsForm is not subclass of {}".format(new_cls, FormModel))

        # register plugin
        VersionHub._register_plugin(new_cls)

        return new_cls


class Plugin(metaclass=PluginMeta):
    _EMPTY_SCHEMA = {"type": "object", "properties": {}, "required": [], "definitions": {}}

    def __init__(self):
        self._poll_interval = -1
        self.is_waiting_callback = False

    class Error(Exception):
        pass

    def execute(self, inputs: InputsModel, context: Context):
        raise NotImplementedError()

    def wait_poll(self, interval: int):
        self.is_waiting_callback = False
        self._poll_interval = max(interval, 0)

    def wait_callback(self):
        self._poll_interval = -1
        self.is_waiting_callback = True

    @property
    def is_wating_poll(self) -> bool:
        return self._poll_interval != -1

    @property
    def poll_interval(self) -> int:
        return self._poll_interval

    @staticmethod
    def prepare_callback(context: Context) -> CallbackPreparation:

        return prepare_callback(context.trace_id)

    @classmethod
    def _trim_schema(cls, schema) -> dict:
        return {
            "type": schema["type"],
            "properties": schema["properties"],
            "required": schema.get("required", []),
            "definitions": schema.get("definitions", {}),
        }

    @classmethod
    def dict(cls) -> dict:
        data = {
            "desc": getattr(cls.Meta, "desc", ""),
            "version": cls.Meta.version,
            "enable_plugin_callback": getattr(cls.Meta, "enable_plugin_callback", False),
            "inputs": cls._EMPTY_SCHEMA,
            "outputs": cls._EMPTY_SCHEMA,
            "context_inputs": cls._EMPTY_SCHEMA,
            "forms": {
                "renderform": cls.renderform,
            },
        }

        inputs_cls = getattr(cls, "Inputs", None)
        if inputs_cls:
            inputs_schema = cls._trim_schema(inputs_cls.schema())
            # update form fields to json schema
            inputs_form_cls = getattr(cls, "InputsForm", None)
            if inputs_form_cls:
                for attr in inputs_form_cls.fields():
                    inputs_schema["properties"][attr].update(getattr(inputs_form_cls, attr))

            data["inputs"] = inputs_schema

        outputs_cls = getattr(cls, "Outputs", None)
        if outputs_cls:
            data["outputs"] = cls._trim_schema(outputs_cls.schema())

        context_cls = getattr(cls, "ContextInputs", None)
        if context_cls:
            data["context_inputs"] = cls._trim_schema(context_cls.schema())

        return data
