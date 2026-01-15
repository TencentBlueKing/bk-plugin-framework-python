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

import logging

from celery import shared_task

from bk_plugin_framework.kit import State
from bk_plugin_framework.utils import local
from bk_plugin_framework.envs import settings
from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.runtime.executor import BKPluginExecutor
from bk_plugin_framework.runtime.schedule.models import Schedule

logger = logging.getLogger("bk_plugin")


def _set_schedule_state(trace_id: str, state: State):
    try:
        Schedule.objects.filter(trace_id=trace_id).update(state=state.value)
    except Exception:
        logger.exception("[execute] set schedule state error")


@shared_task(ignore_result=True)
def schedule(trace_id: str):
    local.set_trace_id(trace_id)

    try:
        schedule = Schedule.objects.get(trace_id=trace_id)
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
