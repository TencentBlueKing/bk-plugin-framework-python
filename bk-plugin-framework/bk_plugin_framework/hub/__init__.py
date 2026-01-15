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

import os
import typing
import logging
from bk_plugin_framework.utils.module_load import load_form_module_path

logger = logging.getLogger("bk-plugin-framework")


class VersionHub:
    __hub = {}

    @classmethod
    def _register_plugin(cls, plugin_cls: typing.Type):
        version = plugin_cls.Meta.version
        existed_plugin_cls = cls.__hub.get(version)
        if existed_plugin_cls:
            raise RuntimeError(
                "plugin register error, {}'s version {} conflict with {}".format(
                    existed_plugin_cls, version, plugin_cls
                )
            )

        cls.__hub[version] = plugin_cls
        form_module_path = load_form_module_path()
        if form_module_path is None:
            raise RuntimeError("can not find bk_plugin module for plugin {}".format(plugin_cls))

        form_dir = os.path.join(form_module_path, version)
        form_path = os.path.join(form_dir, "form.js")

        try:
            with open(form_path, encoding="utf-8") as form_file:
                version_form = form_file.read()
            plugin_cls.renderform = version_form
        except FileNotFoundError:
            plugin_cls.renderform = None
            logger.warning("form file locate error, can't not find {} for {}:{}".format(form_path, plugin_cls, version))

    @classmethod
    def _clear(cls):
        cls.__hub = {}

    @classmethod
    def all_plugins(cls) -> typing.Dict[str, typing.Type]:
        plugins = {}
        for version, plugin_cls in cls.__hub.items():
            plugins[version] = plugin_cls
        return plugins

    @classmethod
    def versions(cls) -> typing.List[str]:
        return sorted(cls.__hub.keys(), reverse=True)
