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
import sys
import typing
import pkgutil
import logging
from importlib import import_module

logger = logging.getLogger("bk-plugin-framework")


def list_all_modules(module_dir: str, sub_dir: str = None) -> typing.List[str]:
    modules = []
    for _, name, is_pkg in pkgutil.iter_modules([module_dir]):
        if name.startswith("_"):
            continue
        module = name if sub_dir is None else "{}.{}".format(sub_dir, name)
        if is_pkg:
            modules += list_all_modules(os.path.join(module_dir, name), module)
        else:
            modules.append(module)
    return modules


def discover_plugins(module):
    module_dir = module.__path__[0]
    sys.path_importer_cache.pop(module_dir, None)
    modules = list_all_modules(module_dir)
    for name in modules:
        module_path = "{}.{}".format(module.__name__, name)
        import_module(module_path)


def load_form_module_path():
    try:
        plugin_module = import_module("bk_plugin")
    except ImportError as e:
        logger.warning("form module locate failed, standard bk_plugin module load error: %s" % e)
        return None

    return os.path.join(os.path.abspath(plugin_module.__file__).rsplit(os.sep, 1)[0], "forms")
