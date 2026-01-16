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

from unittest.mock import MagicMock, patch

from bk_plugin_framework.hub import VersionHub


@patch("bk_plugin_framework.hub.load_form_module_path", MagicMock(return_value="tests"))
def test_version_hub():
    # prepare
    plugin_cls = MagicMock()
    plugin_cls.Meta.version = "1.0.0"

    new_plugin_cls = MagicMock()
    new_plugin_cls.Meta.version = "1.2.0"

    # register
    VersionHub._register_plugin(plugin_cls)

    # repeat
    try:
        VersionHub._register_plugin(plugin_cls)
    except RuntimeError:
        pass

    assert VersionHub.versions() == ["1.0.0"]
    assert VersionHub.all_plugins() == {
        "1.0.0": plugin_cls,
    }

    # new version
    VersionHub._register_plugin(new_plugin_cls)

    assert VersionHub.versions() == ["1.2.0", "1.0.0"]
    assert VersionHub.all_plugins() == {
        "1.0.0": plugin_cls,
        "1.2.0": new_plugin_cls,
    }
