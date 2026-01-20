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
import shutil
import time

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

        # 用于记录各步骤耗时（毫秒）
        step_timings = {}

        # 1. 生成 definition.yaml 文件
        step_start = time.time()
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

        # 输出生成的文件路径
        resources_yaml_path = os.path.join(settings.BASE_DIR, "resources.yaml")
        definition_yaml_path = os.path.join(settings.BASE_DIR, "definition.yaml")
        self.stdout.write(f"[Sync] Generated definition.yaml path: {definition_yaml_path}")

        step_timings["1. 生成 definition.yaml 文件"] = (time.time() - step_start) * 1000

        # 1.1 复制 support-files/resources.yaml 到项目根目录
        # 注意：不再使用 generate_resources_yaml 命令扫描 URL 模块
        # plugin_api/ 和 openapi/ 等接口已在 support-files/resources.yaml 中通过子路径匹配方式定义
        step_start = time.time()
        self._copy_support_files_resources()
        self.stdout.write(f"[Sync] resources.yaml path: {resources_yaml_path}")
        step_timings["1.1 复制 support-files/resources.yaml"] = (time.time() - step_start) * 1000

        # 2. 计算当前哈希值（仅计算 resources.yaml）
        step_start = time.time()
        current_hash = self._calculate_resources_hash()
        self.stdout.write(f"[Sync] Current resources.yaml hash: {current_hash[:16]}...")
        step_timings["2. 计算当前哈希值"] = (time.time() - step_start) * 1000

        # 3. 获取上次同步的哈希值
        step_start = time.time()
        last_hash = self._get_last_sync_hash()
        if last_hash:
            self.stdout.write(f"[Sync] Last sync hash: {last_hash[:16]}...")
        else:
            self.stdout.write("[Sync] No previous sync record found")
        step_timings["3. 获取上次同步的哈希值"] = (time.time() - step_start) * 1000

        # 4. 对比决定是否同步
        step_start = time.time()
        need_sync = force_sync or current_hash != last_hash
        if not need_sync:
            self.stdout.write(self.style.SUCCESS("[Sync] API definition unchanged, skip sync to apigateway"))
            # 仍然获取公钥，确保公钥是最新的
            self._fetch_public_key()
            step_timings["4. 对比决定是否同步"] = (time.time() - step_start) * 1000
            # 打印耗时统计
            self._print_timing_stats(step_timings)
            return
        step_timings["4. 对比决定是否同步"] = (time.time() - step_start) * 1000

        if force_sync:
            self.stdout.write(self.style.WARNING("[Sync] Force sync enabled"))
        else:
            self.stdout.write(self.style.WARNING("[Sync] API definition changed, start syncing..."))

        # 5. 执行同步
        step_start = time.time()
        self.stdout.write("[Sync] sync to apigateway")
        try:
            call_command("sync_drf_apigateway")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"run sync_drf_apigateway fail: {e}"))
            # 同步失败时更新状态
            self._save_sync_hash(current_hash, success=False)
            raise SystemExit(1)
        step_timings["5. 执行同步"] = (time.time() - step_start) * 1000

        # 6. 获取公钥
        step_start = time.time()
        self._fetch_public_key()
        step_timings["6. 获取公钥"] = (time.time() - step_start) * 1000

        # 7. 更新哈希值
        step_start = time.time()
        self._save_sync_hash(current_hash, success=True)
        self.stdout.write(self.style.SUCCESS("[Sync] API gateway sync completed successfully"))
        step_timings["7. 更新哈希值"] = (time.time() - step_start) * 1000

        # 打印耗时统计
        self._print_timing_stats(step_timings)

    def _print_timing_stats(self, step_timings):
        """打印各步骤耗时统计"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("[Sync] 各步骤耗时统计（毫秒）:"))
        self.stdout.write("=" * 50)
        total_time = 0
        for step_name, duration in step_timings.items():
            self.stdout.write(f"  {step_name}: {duration:.2f} ms")
            total_time += duration
        self.stdout.write("-" * 50)
        self.stdout.write(f"  总耗时: {total_time:.2f} ms")
        self.stdout.write("=" * 50 + "\n")

    def _copy_support_files_resources(self):
        """
        将 support-files/resources.yaml 复制到项目根目录作为 resources.yaml

        说明：
        - 不再使用 generate_resources_yaml 命令自动扫描 URL 模块
        - plugin_api/ 和 openapi/ 等接口已在 support-files/resources.yaml 中
          通过子路径匹配（matchSubpath: true）的方式统一定义
        - 这样可以避免扫描 bk_plugin.apis.urls 和 bk_plugin.openapi.urls 模块
        """
        support_files_dir = os.path.join(os.path.dirname(__file__), "support-files")
        support_filepath = os.path.join(support_files_dir, "resources.yaml")
        target_filepath = os.path.join(settings.BASE_DIR, "resources.yaml")

        # 检查 support-files/resources.yaml 是否存在
        if not os.path.exists(support_filepath):
            self.stderr.write(self.style.ERROR(f"[Sync] support-files/resources.yaml not found: {support_filepath}"))
            raise SystemExit(1)

        try:
            # 直接复制文件
            shutil.copy2(support_filepath, target_filepath)
            self.stdout.write(self.style.SUCCESS(f"[Sync] Copied support-files/resources.yaml to {target_filepath}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"[Sync] Failed to copy support-files/resources.yaml: {e}"))
            raise SystemExit(1)

    def _calculate_resources_hash(self):
        """
        计算 resources.yaml 的哈希值

        注意：为了避免 YAML 内容顺序变化导致的 hash 不一致问题，
        这里先将 YAML 解析为字典，然后用 sort_keys=True 重新序列化，
        确保相同内容的 YAML 文件总是产生相同的 hash 值。
        """
        filepath = os.path.join(settings.BASE_DIR, "resources.yaml")
        if os.path.exists(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data:
                    # 使用 sort_keys=True 确保输出顺序一致
                    # 这样即使原始文件中 A,B,C 和 B,C,A 的顺序不同，
                    # 规范化后的内容也会相同，从而产生相同的 hash
                    normalized_content = yaml.dump(
                        data, default_flow_style=False, allow_unicode=True, sort_keys=True  # 关键：排序所有 key
                    )
                    return hashlib.sha256(normalized_content.encode()).hexdigest()
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"[Sync] Failed to normalize resources.yaml for hash: {e}, fallback to raw content hash"
                    )
                )
                # 回退到原始方式
                with open(filepath, encoding="utf-8") as f:
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
