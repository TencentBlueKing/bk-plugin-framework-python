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

from pathlib import Path

import yaml
from django.template import Context, Engine


RESOURCE_TEMPLATE = (
    Path(__file__).parents[3]
    / "bk_plugin_framework"
    / "services"
    / "bpf_service"
    / "management"
    / "commands"
    / "support-files"
    / "resources.yaml"
)


class TestGatewayResources:
    def test_schedule_resource_is_public_and_requires_app_auth_only(self):
        engine = Engine()
        expected_backend_paths = [
            ("", "/bk_plugin/schedule/{id}"),
            ("subpath", "/{env.api_sub_path}/bk_plugin/schedule/{id}"),
        ]

        for backend_sub_path, expected_backend_path in expected_backend_paths:
            rendered = engine.from_string(RESOURCE_TEMPLATE.read_text(encoding="utf-8")).render(
                Context({"settings": {"BK_PLUGIN_APIGW_BACKEND_SUB_PATH": backend_sub_path}})
            )
            resource = yaml.safe_load(rendered)["paths"]["/bk_plugin/schedule/{id}"]["get"]["x-bk-apigateway-resource"]

            assert resource["isPublic"] is True
            assert resource["allowApplyPermission"] is True
            assert resource["authConfig"] == {
                "userVerifiedRequired": False,
                "appVerifiedRequired": True,
                "resourcePermissionRequired": False,
            }
            assert resource["backend"]["path"] == expected_backend_path
