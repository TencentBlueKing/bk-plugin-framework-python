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

# DO NOT MODIFY THIS FILE UNLESS YOU KNOW WHAT YOU ARE DOING !!!

import os
import sys

# 将项目根目录添加到 Python 路径，使 Python 能直接引用本地的 bk_plugin_runtime 和 bk_plugin_framework
# 部署时代码在 /app 目录，bin/manage.py 在 /app/bin/ 下，所以取上级目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bk_plugin_runtime.settings")
    os.environ.setdefault("BK_APP_CONFIG_PATH", "bk_plugin_runtime.config")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
