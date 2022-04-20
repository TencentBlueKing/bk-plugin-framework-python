# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import os

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    def prepare_devlop_env(self):
        os.environ.setdefault("BK_INIT_SUPERUSER", "admin")
        os.environ.setdefault("BK_PAAS2_URL", "")
        os.environ.setdefault("BKPAAS_MAJOR_VERSION", "3")
        os.environ.setdefault("BK_APIGW_MANAGER_URL_TEMPL", "")

        for env in [
            "BK_INIT_SUPERUSER",
            "DJANGO_SETTINGS_MODULE",
            "BK_APP_CONFIG_PATH",
            "BKPAAS_ENGINE_REGION",
            "BKPAAS_LOGIN_URL",
            "BKPAAS_MAJOR_VERSION",
        ]:
            if not os.getenv(env):
                raise ValueError(
                    "the value of environment variable {} is empty or not set, please check again.".format(env)
                )

    def handle(self, *args, **kwargs):
        self.prepare_devlop_env()
        call_command("runserver", *args, **kwargs)
