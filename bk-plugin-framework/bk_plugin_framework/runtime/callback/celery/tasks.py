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
import json
import logging
import random
import time

from celery import shared_task, current_app

from bk_plugin_framework.kit import State
from bk_plugin_framework.metrics import BK_PLUGIN_CALLBACK_EXCEPTION_COUNT, HOSTNAME, BK_PLUGIN_CALLBACK_TIME
from bk_plugin_framework.utils import local
from bk_plugin_framework.envs import settings
from bk_plugin_framework.hub import VersionHub
from bk_plugin_framework.runtime.executor import BKPluginExecutor
from bk_plugin_framework.runtime.schedule.models import Schedule
from bk_plugin_framework.runtime.schedule.utils import get_schedule_lock

logger = logging.getLogger("bk_plugin")


def _set_schedule_state(trace_id: str, state: State):
    try:
        Schedule.objects.filter(trace_id=trace_id).update(state=state.value)
    except Exception:
        logger.exception("[execute] set schedule state error")


@shared_task(ignore_result=True)
def callback(trace_id: str, callback_id: str, callback_data: str):
    with get_schedule_lock(trace_id) as lock:
        if not lock.locked:
            try_after = random.randint(1, 5)
            current_app.tasks[settings.CALLBACK_TASK_NAME].apply_async(
                kwargs={"trace_id": trace_id, "callback_id": callback_id, "callback_data": callback_data},
                countdown=try_after,
                queue="plugin_callback",
            )
            return

        start = time.perf_counter()

        local.set_trace_id(trace_id)

        try:
            schedule = Schedule.objects.get(trace_id=trace_id)
        except Exception:
            logger.exception("[callback_task] fetch schedule/callback obj %s failed" % trace_id)
            _set_schedule_state(trace_id=trace_id, state=State.FAIL)
            return

        if schedule.state is not State.CALLBACK.value:
            logger.exception(
                "[callback_task] schedule state[%s] is not CALLBACK,trace_id[%s]" % (schedule.state, trace_id)
            )
            return

        plugin_cls = VersionHub.all_plugins().get(schedule.plugin_version)
        if not plugin_cls:
            logger.error("[callback_task] can not find plugin class for version %s" % schedule.plugin_version)
            _set_schedule_state(trace_id=trace_id, state=State.FAIL)

        executor = BKPluginExecutor(trace_id=trace_id)

        callback_info = {"callback_id": callback_id, "callback_data": json.loads(callback_data)}
        try:
            executor.schedule(plugin_cls=plugin_cls, schedule=schedule, callback_info=callback_info)
        except Exception:
            BK_PLUGIN_CALLBACK_EXCEPTION_COUNT.labels(hostname=HOSTNAME, version=schedule.plugin_version).inc()
            logger.exception("[callback_task] executor schedule raise unexpected error")
            _set_schedule_state(trace_id=trace_id, state=State.FAIL)

        BK_PLUGIN_CALLBACK_TIME.labels(hostname=HOSTNAME, version=schedule.plugin_version).observe(
            time.perf_counter() - start)
