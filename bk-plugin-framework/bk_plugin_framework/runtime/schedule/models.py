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

from django.db import models
from django.utils import timezone


class ScheduleManger(models.Manager):
    def apply_schedule_lock(self, trace_id: str) -> bool:
        """
        获取 Schedule 对象的调度锁，返回是否成功获取锁

        :return: True or False
        """
        return self.filter(trace_id=trace_id, scheduling=False).update(scheduling=True) == 1

    def release_schedule_lock(self, trace_id: str) -> None:
        """
        释放指定 Schedule 的调度锁
        :return:
        """
        self.filter(trace_id=trace_id, scheduling=True).update(scheduling=False)

    def delete_expired_schedule(self, interval: int) -> int:
        """
        清理过期的Schedule
        :param interval:
        :return: count
        """
        expired_date = timezone.now() + timezone.timedelta(days=(-interval))
        rows = self.filter(finish_at__lt=expired_date).delete()[0]
        return rows


class Schedule(models.Model):
    trace_id = models.CharField("trace id", max_length=33, primary_key=True)
    plugin_version = models.CharField("plugin version", max_length=128)
    state = models.IntegerField("execution state")
    invoke_count = models.IntegerField("invoke count", default=1)
    data = models.TextField("context and inputs")
    scheduling = models.BooleanField("是否正在调度", default=False)
    err = models.TextField("schedule error message", default="")
    created_at = models.DateTimeField("create time", auto_now_add=True)
    finish_at = models.DateTimeField("finish time", null=True)

    objects = ScheduleManger()
