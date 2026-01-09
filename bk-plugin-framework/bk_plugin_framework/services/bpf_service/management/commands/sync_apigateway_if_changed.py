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

import hashlib
import os

import yaml
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "仅在接口定义发生变化时同步到API网关"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="强制同步，忽略哈希值对比",
        )

    def handle(self, *args, **options):
        force_sync = options.get("force", False)

        # 1. 生成 yaml 文件
        self.stdout.write("[Sync] generate definition.yaml")
        try:
            call_command("generate_definition_yaml")
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"run generate_definition_yaml fail: {e}, "
                    "please run this command on your development env to find out the reason"
                )
            )
            raise SystemExit(1)

        self.stdout.write("[Sync] generate resources.yaml")
        try:
            call_command("generate_resources_yaml")
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"run generate_resources_yaml fail: {e}, "
                    "please run this command on your development env to find out the reason"
                )
            )
            raise SystemExit(1)

        # 1.1 追加 plugin_api 资源配置
        self._append_plugin_api_resource()

        # 2. 计算当前哈希值（仅计算 resources.yaml）
        current_hash = self._calculate_resources_hash()
        self.stdout.write(f"[Sync] Current resources.yaml hash: {current_hash[:16]}...")

        # 3. 获取上次同步的哈希值
        last_hash = self._get_last_sync_hash()
        if last_hash:
            self.stdout.write(f"[Sync] Last sync hash: {last_hash[:16]}...")
        else:
            self.stdout.write("[Sync] No previous sync record found")

        # 4. 对比决定是否同步
        if not force_sync and current_hash == last_hash:
            self.stdout.write(self.style.SUCCESS("[Sync] API definition unchanged, skip sync to apigateway"))
            # 仍然获取公钥，确保公钥是最新的
            self._fetch_public_key()
            return

        if force_sync:
            self.stdout.write(self.style.WARNING("[Sync] Force sync enabled"))
        else:
            self.stdout.write(self.style.WARNING("[Sync] API definition changed, start syncing..."))

        # 5. 执行同步
        self.stdout.write("[Sync] sync to apigateway")
        try:
            call_command("sync_drf_apigateway")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"run sync_drf_apigateway fail: {e}"))
            # 同步失败时更新状态
            self._save_sync_hash(current_hash, success=False)
            raise SystemExit(1)

        # 6. 获取公钥
        self._fetch_public_key()

        # 7. 更新哈希值
        self._save_sync_hash(current_hash, success=True)
        self.stdout.write(self.style.SUCCESS("[Sync] API gateway sync completed successfully"))

    def _append_plugin_api_resource(self):
        """在 resources.yaml 的 paths 节点下追加 plugin_api 资源配置"""
        filepath = os.path.join(settings.BASE_DIR, "resources.yaml")
        if not os.path.exists(filepath):
            self.stdout.write(self.style.WARNING(f"[Sync] {filepath} not found, skip appending plugin_api"))
            return

        try:
            # 读取现有内容，检查是否已存在
            with open(filepath) as f:
                content = f.read()

            plugin_api_path = "/bk_plugin/plugin_api/:"
            if plugin_api_path in content:
                self.stdout.write("[Sync] plugin_api resource already exists, skip appending")
                return

            # 根据 settings.BK_PLUGIN_APIGW_BACKEND_SUB_PATH 决定 backend path
            if getattr(settings, "BK_PLUGIN_APIGW_BACKEND_SUB_PATH", False):
                backend_path = "/{env.api_sub_path}bk_plugin/plugin_api/"
            else:
                backend_path = "/bk_plugin/plugin_api/"

            # 使用 YAML 解析来正确插入
            data = yaml.safe_load(content)

            if "paths" not in data:
                self.stdout.write(self.style.WARNING("[Sync] 'paths' not found in resources.yaml, skip appending"))
                return

            # 在 paths 下添加 plugin_api 路径
            data["paths"]["/bk_plugin/plugin_api/"] = {
                "x-bk-apigateway-method-any": {
                    "operationId": "plugin_api",
                    "description": "",
                    "tags": [],
                    "responses": {"default": {"description": ""}},
                    "x-bk-apigateway-resource": {
                        "isPublic": True,
                        "allowApplyPermission": True,
                        "matchSubpath": True,
                        "backend": {
                            "type": "HTTP",
                            "method": "any",
                            "path": backend_path,
                            "matchSubpath": True,
                            "timeout": 0,
                            "upstreams": {},
                            "transformHeaders": {},
                        },
                        "authConfig": {"userVerifiedRequired": True, "appVerifiedRequired": False},
                        "disabledStages": [],
                    },
                }
            }

            # 写回文件（使用 yaml.dump 保持格式）
            with open(filepath, "w") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            self.stdout.write(self.style.SUCCESS("[Sync] plugin_api resource appended to resources.yaml"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"[Sync] Failed to append plugin_api resource: {e}"))

    def _print_yaml_content(self, filepath, name):
        """打印 YAML 文件内容"""
        if os.path.exists(filepath):
            self.stdout.write(f"[Sync] the {filepath} content:")
            with open(filepath) as f:
                self.stdout.write(f.read())
            self.stdout.write("====================")

    def _calculate_resources_hash(self):
        """计算 resources.yaml 的哈希值"""
        filepath = os.path.join(settings.BASE_DIR, "resources.yaml")
        if os.path.exists(filepath):
            with open(filepath) as f:
                content = f.read()
            return hashlib.sha256(content.encode()).hexdigest()
        return ""

    def _get_last_sync_hash(self):
        """从数据库获取上次同步的哈希值"""
        try:
            from bk_plugin_framework.services.bpf_service.models import (
                APIGatewaySyncState,
            )

            state = APIGatewaySyncState.objects.filter(sync_success=True).first()
            return state.api_hash if state else ""
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[Sync] Failed to get last sync hash: {e}"))
            return ""

    def _save_sync_hash(self, hash_value, success=True):
        """保存哈希值到数据库"""
        try:
            from bk_plugin_framework.services.bpf_service.models import (
                APIGatewaySyncState,
            )

            # 使用 update_or_create，保证只有一条记录
            APIGatewaySyncState.objects.update_or_create(
                pk=1, defaults={"api_hash": hash_value, "sync_success": success}
            )
            self.stdout.write(f"[Sync] Sync state saved (success={success})")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[Sync] Failed to save sync hash: {e}"))

    def _fetch_public_key(self):
        """获取 API 网关公钥"""
        self.stdout.write("[Sync] fetch the public key")
        try:
            call_command("fetch_apigw_public_key")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"run fetch_apigw_public_key fail: {e}"))
            raise SystemExit(1)
