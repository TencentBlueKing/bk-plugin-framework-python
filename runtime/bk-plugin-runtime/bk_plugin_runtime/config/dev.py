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
import MySQLdb
from bk_plugin_runtime.config import RUN_VER

if RUN_VER == "open":
    from blueapps.patch.settings_open_saas import *  # noqa
else:
    from blueapps.patch.settings_paas_services import *  # noqa

# 本地开发环境
RUN_MODE = "DEVELOP"

# APP本地静态资源目录
STATIC_URL = "/static/"

# APP静态资源目录url
# REMOTE_STATIC_URL = '%sremote/' % STATIC_URL

# Celery 消息队列设置 RabbitMQ
# BROKER_URL = 'amqp://guest:guest@localhost:5672//'
# Celery 消息队列设置 Redis
BROKER_URL = os.getenv("BK_PLUGIN_RUNTIME_BROKER_URL")

DEBUG = True

# 本地开发数据库默认使用sqlite3
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": APP_CODE  # noqa
    },
}
# 本地开发是否使用mysql数据库
BK_PLUGIN_DEV_USE_MYSQL = os.getenv("BK_PLUGIN_DEV_USE_MYSQL")

# 兼容bk-plugin-framework<=0.8.3,本地开发使用mysql的情况
is_exist_mysql = False
try:
    connect = MySQLdb.connect(
        host=os.getenv("BK_PLUGIN_RUNTIME_DB_HOST"),
        port=int(os.getenv("BK_PLUGIN_RUNTIME_DB_PORT")),
        user=os.getenv("BK_PLUGIN_RUNTIME_DB_USER"),
        passwd=os.getenv("BK_PLUGIN_RUNTIME_DB_PWD"),
        db=APP_CODE,  # noqa
    )
    connect.close()
    is_exist_mysql = True
except Exception:
    pass

# 如果存在 BK_PLUGIN_DEV_USE_MYSQL 配置，则以 BK_PLUGIN_DEV_USE_MYSQL 为准
# 如果不存在 BK_PLUGIN_DEV_USE_MYSQL 配置，但是 is_exist_mysql 为 True，则使用 MySQL
# 如果不存在 BK_PLUGIN_DEV_USE_MYSQL 配置，且 is_exist_mysql 为 False，则使用 SQLite
if (int(BK_PLUGIN_DEV_USE_MYSQL or 0)) or (BK_PLUGIN_DEV_USE_MYSQL is None and is_exist_mysql):
    # USE FOLLOWING SQL TO CREATE THE DATABASE NAMED APP_CODE
    # SQL: CREATE DATABASE `bk-plugin-demo` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci; # noqa: E501
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": APP_CODE,  # noqa
            "USER": os.getenv("BK_PLUGIN_RUNTIME_DB_USER"),
            "PASSWORD": os.getenv("BK_PLUGIN_RUNTIME_DB_PWD"),
            "HOST": os.getenv("BK_PLUGIN_RUNTIME_DB_HOST"),
            "PORT": os.getenv("BK_PLUGIN_RUNTIME_DB_PORT"),
        },
    }

default.logging_addition_settings(LOGGING)  # noqa

# 本地开发豁免 APIGW 来源校验
BK_APIGW_REQUIRE_EXEMPT = True

# 插件开发者自定义配置变量
try:
    from bk_plugin.settings import *  # noqa
except ImportError:
    pass

# 多人开发时，无法共享的本地配置可以放到新建的 local_settings.py 文件中
# 并且把 local_settings.py 加入版本管理忽略文件中
try:
    from local_settings import *  # noqa
except ImportError:
    pass
