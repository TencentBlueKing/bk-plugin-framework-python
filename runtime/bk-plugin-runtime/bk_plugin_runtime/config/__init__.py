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

from __future__ import absolute_import

__all__ = ["celery_app", "RUN_VER", "APP_CODE", "SECRET_KEY", "BK_URL", "BASE_DIR"]

import os

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
import django
from blueapps.core.celery import celery_app
from django.utils.functional import cached_property
from django.db.backends.mysql.features import DatabaseFeatures

# app 基本信息


def get_env_or_raise(key):
    """Get an environment variable, if it does not exist, raise an exception"""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(
            (
                'Environment variable "{}" not found, you must set this variable to run this application.'
            ).format(key)
        )
    return value


# 应用 ID
APP_CODE = get_env_or_raise("BKPAAS_APP_ID")
# 应用用于调用云 API 的 Secret
SECRET_KEY = get_env_or_raise("BKPAAS_APP_SECRET")

# SaaS运行版本，如非必要请勿修改
RUN_VER = "ieod" if os.getenv("BKPAAS_ENGINE_REGION", "open") == "ieod" else "open"
# 蓝鲸SaaS平台URL，例如 http://paas.bking.com
BK_URL = None

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 兼容低版本 MySQL
class PatchFeatures:
    @cached_property
    def minimum_database_version(self):
        django_version = django.VERSION
        if self.connection.mysql_is_mariadb:
            return 10, 4
        else:
            return 5, 7

# 目前 Django 仅是对 5.7 做了软性的不兼容改动，在没有使用 8.0 特异的功能时，对 5.7 版本的使用无影响
DatabaseFeatures.minimum_database_version = PatchFeatures.minimum_database_version
