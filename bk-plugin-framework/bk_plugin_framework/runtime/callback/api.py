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
import uuid
import time
import json
import logging

from django.conf import settings as default_settings
from celery import current_app
from cryptography.fernet import Fernet

from bk_plugin_framework.envs import settings
from bk_plugin_framework.runtime.schedule.models import Schedule
from bk_plugin_framework.constants import State

logger = logging.getLogger("bk_plugin")


class CallbackPreparation(object):
    def __init__(self, callback_id: str, callback_url: str):
        self.id = callback_id
        self.url = callback_url


def callback(trace_id: str, callback_id: str, callback_data: dict) -> dict:
    """
    派发回调任务，回调任务被拉起执行时应该调用 callback 的celery任务
    :param trace_id:
    :param callback_id:
    :param callback_data:
    :return: {
        "result": True,
        "message": "callback success"
    }
    """
    for _ in range(settings.PLUGIN_CALLBACK_RETRY_TIMES):
        try:
            schedule_state = Schedule.objects.filter(trace_id=trace_id).values_list("state", flat=True).first()
            if schedule_state is State.CALLBACK.value:
                current_app.tasks[settings.CALLBACK_TASK_NAME].apply_async(
                    kwargs={
                        "trace_id": trace_id,
                        "callback_id": callback_id,
                        "callback_data": json.dumps(callback_data),
                    },
                    queue="plugin_callback",
                )

                logger.info("callback_id={},trace_id={} callback success".format(callback_id, trace_id))

                return {"result": True, "message": "callback success"}

            else:
                message = "callback fail,schedule plugin state[{}]: is not callback".format(schedule_state)

        except Exception as e:
            message = "callback fail,unknown error,exception:{}".format(str(e))
            logger.exception(e)

        logger.warning(
            "callback_id={},trace_id={} callback retry,error_message:{}".format(callback_id, trace_id, message)
        )
        time.sleep(0.5)

    return {"result": False, "message": message}


def prepare_callback(trace_id: str) -> CallbackPreparation:
    """
    回调前预处理,生成回调的url和id
    :param trace_id:
    :return: CallbackPreparation
    """
    callback_id = uuid.uuid4().hex

    f = Fernet(settings.BK_PLUGIN_CALLBACK_KEY)
    token = f.encrypt(bytes("{}:{}".format(callback_id, trace_id), encoding="utf8")).decode()
    callback_url = "{}/{}/callback/{}/".format(
        settings.BK_PLUGIN_CALLBACK_HOST.rstrip("/"), default_settings.BK_PLUGIN_APIGW_STAGE_NAME, token
    )

    return CallbackPreparation(callback_id, callback_url)


def parse_callback_token(token: str) -> dict:
    """
    解析第三方系统回调传入的token是否有效
    :param token:
    :return: {
        "result": True
        "data":{
            "callback_id":"",
            "trace_id":"",
        }
    }
    """
    try:
        f = Fernet(settings.BK_PLUGIN_CALLBACK_KEY)
        callback_id, trace_id = f.decrypt(bytes(token, encoding="utf8")).decode().split(":")
        if not len(callback_id) == len(trace_id) == 32:
            message = "trace_id[{}] or callback_id[{}] 不合法".format(trace_id, callback_id)
            logger.warning(message)
            return {"result": False, "message": message}

        return {"result": True, "data": {"callback_id": callback_id, "trace_id": trace_id}}
    except Exception:
        message = "invalid token {}".format(token)
        logger.warning(message)
        return {"result": False, "message": message}
