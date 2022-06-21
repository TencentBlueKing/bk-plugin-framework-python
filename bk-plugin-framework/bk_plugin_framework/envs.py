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
import base64
import hashlib
import logging

from pydantic import BaseSettings
from django.conf import settings as default_settings

logger = logging.getLogger("bk-plugin")


def compute_settings(settings: BaseSettings) -> dict:
    """
    对需要计算的环境变量进行计算
    :param settings:
    :return:
    """
    try:
        callback_key = base64.urlsafe_b64encode(
            hashlib.sha256(default_settings.BK_APP_SECRET.encode("utf-8")).hexdigest()[:32].encode()
        )
    except Exception as e:
        logger.exception("get CALLBACK_KEY fail")
        raise Exception(e)

    callback_host = "http://{}".format(default_settings.BK_PLUGIN_APIGW_BACKEND_HOST)

    BKPAAS_ENVIRONMENT = os.getenv("BKPAAS_ENVIRONMENT", "dev")
    BKPAAS_ENGINE_REGION = os.getenv("BKPAAS_ENGINE_REGION", "open")

    if BKPAAS_ENGINE_REGION == "ieod":
        user_token_key_name = "bk_ticket" if BKPAAS_ENVIRONMENT == "dev" else "jwt"
    else:
        user_token_key_name = "bk_token" if BKPAAS_ENVIRONMENT == "dev" else "jwt"

    return {
        "BK_PLUGIN_CALLBACK_KEY": callback_key,
        "BK_PLUGIN_CALLBACK_HOST": callback_host,
        "USER_TOKEN_KEY_NAME": user_token_key_name,
    }


class Settings(BaseSettings):
    BKPAAS_ENVIRONMENT: str = "dev"
    BK_PLUGIN_CACHE_TIMEOUT: int = 60 * 60 * 24
    BK_PLUGIN_CALLBACK_KEY: str = ""
    BK_PLUGIN_CALLBACK_HOST: str = ""
    PLUGIN_CALLBACK_RETRY_TIMES: int = 3
    CALLBACK_TASK_NAME: str = "bk_plugin_framework.runtime.callback.celery.tasks.callback"
    SCHEDULE_PERSISTENT_DAYS: int = 30
    USER_TOKEN_KEY_NAME: str = ""

    class Config:
        case_sensitive = True

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                compute_settings,
                file_secret_settings,
            )


settings = Settings()
