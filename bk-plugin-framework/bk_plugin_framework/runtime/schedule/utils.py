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
from bk_plugin_framework.runtime.schedule.models import Schedule


class ScheduleLock(object):
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.locked = False

    def __enter__(self):
        self.locked = Schedule.objects.apply_schedule_lock(self.trace_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.locked:
            Schedule.objects.release_schedule_lock(self.trace_id)


def get_schedule_lock(trace_id: str) -> ScheduleLock:
    """
    获取 schedule lock 的 context 对象
    :param trace_id:
    :return:
    """
    return ScheduleLock(trace_id)
