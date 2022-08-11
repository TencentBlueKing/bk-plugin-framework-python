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

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        definition_file_path = os.path.join(__file__.rsplit("/", 1)[0], "data/api-definition.yml")
        resources_file_path = os.path.join(__file__.rsplit("/", 1)[0], "data/api-resources.yml")
        print("[bk-plugin-framework]call sync_apigw_stage with definition: %s" % definition_file_path)
        call_command("sync_apigw_stage", file=definition_file_path)
        print("[bk-plugin-framework]call sync_apigw_resources with resources: %s" % resources_file_path)
        call_command("sync_apigw_resources", file=resources_file_path)
        print("[bk-plugin-framework]call sync_apigw_strategies with definition: %s" % definition_file_path)
        call_command("sync_apigw_strategies", file=definition_file_path)
        print("[bk-plugin-framework]call create_version_and_release_apigw with definition: %s" % definition_file_path)
        call_command(
            "create_version_and_release_apigw", file=definition_file_path, stage=[settings.BK_PLUGIN_APIGW_STAGE_NAME]
        )
