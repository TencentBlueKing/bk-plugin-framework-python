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

import logging

from celery import shared_task
from django.db import InterfaceError, OperationalError

from bk_plugin_framework.envs import settings
from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.kit import State
from bk_plugin_framework.runtime.executor import BKPluginExecutor
from bk_plugin_framework.runtime.schedule.models import Schedule
from bk_plugin_framework.utils import local

logger = logging.getLogger("bk_plugin")

# 瞬时数据库连接类错误：DB 抖动可通过重试自愈，不应直接把调度判定为失败
TRANSIENT_DB_EXC = (OperationalError, InterfaceError)


def _set_schedule_state(trace_id: str, state: State):
    try:
        Schedule.objects.filter(trace_id=trace_id).update(state=state.value)
    except Exception:
        logger.exception("[execute] set schedule state error")


@shared_task(bind=True, ignore_result=True, max_retries=6, default_retry_delay=5)
def schedule(self, trace_id: str):
    local.set_trace_id(trace_id)

    try:
        schedule = Schedule.objects.get(trace_id=trace_id)
    except TRANSIENT_DB_EXC as exc:
        # DB 瞬时不可达：重试本次轮询而非判失败，避免误杀运行中的插件；重试用尽才兜底置失败
        if self.request.retries >= self.max_retries:
            logger.error(
                "[schedule_task] db unreachable, give up fetching schedule obj %s after %s retries"
                % (trace_id, self.request.retries)
            )
            _set_schedule_state(trace_id=trace_id, state=State.FAIL)
            return
        countdown = min(2 ** self.request.retries * 5, 60)
        logger.warning(
            "[schedule_task] transient db error when fetching schedule obj %s (retry=%s), retry in %ss: %s"
            % (trace_id, self.request.retries, countdown, exc)
        )
        raise self.retry(exc=exc, countdown=countdown)
    except Exception:
        logger.exception("[schedule_task] fetch schedule obj %s failed" % trace_id)
        _set_schedule_state(trace_id=trace_id, state=State.FAIL)
        return

    plugin_cls = VersionHub.all_plugins().get(schedule.plugin_version)
    if not plugin_cls:
        logger.error("[schedule_task] can not find plugin class for version %s" % schedule.plugin_version)
        _set_schedule_state(trace_id=trace_id, state=State.FAIL)

    executor = BKPluginExecutor(trace_id=trace_id)

    try:
        executor.schedule(plugin_cls=plugin_cls, schedule=schedule)
    except Exception:
        logger.exception("[schedule_task] executor schedule raise unexpected error")
        _set_schedule_state(trace_id=trace_id, state=State.FAIL)


@shared_task(ignore_result=True)
def delete_expired_schedule():
    logger.info("[delete_expired_schedule] start to delete expire schedule")
    rows = Schedule.objects.delete_expired_schedule(settings.SCHEDULE_PERSISTENT_DAYS)
    logger.info("[delete_expired_schedule] delete {} rows".format(rows))
