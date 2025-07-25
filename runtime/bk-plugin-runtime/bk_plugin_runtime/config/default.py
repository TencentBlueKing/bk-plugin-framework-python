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
import json
import urllib

from blueapps.conf.log import get_logging_config_dict
from blueapps.conf.default_settings import *  # noqa

BKPAAS_ENVIRONMENT = os.getenv("BKPAAS_ENVIRONMENT", "dev")
# 默认关闭可观侧性
ENABLE_OTEL_METRICS = os.getenv("ENABLE_METRICS", False)

# 请在这里加入你的自定义 APP
INSTALLED_APPS += (  # noqa
    "rest_framework",
    "drf_yasg",
    "bk_plugin_framework.runtime.loghub",
    "bk_plugin_framework.runtime.schedule",
    "bk_plugin_framework.runtime.callback",
    "bk_plugin_framework.services.bpf_service",
    "apigw_manager.apigw",
    "django_dbconn_retry",
)
if ENABLE_OTEL_METRICS:
    INSTALLED_APPS += ("blueapps.opentelemetry.instrument_app",)  # noqa

if BKPAAS_ENVIRONMENT == "dev":
    INSTALLED_APPS += ("bk_plugin_framework.services.debug_panel",)  # noqa

from bk_plugin_framework.runtime.schedule.celery import queues as schedule_queues  # noqa
from bk_plugin_framework.runtime.callback.celery import queues as callback_queues  # noqa

CELERY_QUEUES = schedule_queues.CELERY_QUEUES
CELERY_QUEUES.extend(callback_queues.CELERY_QUEUES)

# 这里是默认的中间件，大部分情况下，不需要改动
# 如果你已经了解每个默认 MIDDLEWARE 的作用，确实需要去掉某些 MIDDLEWARE，或者改动先后顺序，请去掉下面的注释，然后修改
# MIDDLEWARE = (
#     # request instance provider
#     'blueapps.middleware.request_provider.RequestProvider',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     # 跨域检测中间件， 默认关闭
#     # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'django.middleware.security.SecurityMiddleware',
#     # 蓝鲸静态资源服务
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     # Auth middleware
#     'blueapps.account.middlewares.WeixinLoginRequiredMiddleware',
#     'blueapps.account.middlewares.LoginRequiredMiddleware',
#     # exception middleware
#     'blueapps.core.exceptions.middleware.AppExceptionMiddleware'
# )

# 自定义中间件
MIDDLEWARE += (  # noqa
    "corsheaders.middleware.CorsMiddleware",
    "bk_plugin_framework.services.bpf_service.middlewares.TraceIDInjectMiddleware",
    "apigw_manager.apigw.authentication.ApiGatewayJWTGenericMiddleware",  # JWT 认证
    "apigw_manager.apigw.authentication.ApiGatewayJWTAppMiddleware",  # JWT 透传的应用信息
)

# 所有环境的日志级别可以在这里配置
# LOG_LEVEL = 'INFO'

#
# 静态资源文件(js,css等）在APP上线更新后, 由于浏览器有缓存,
# 可能会造成没更新的情况. 所以在引用静态资源的地方，都把这个加上
# Django 模板中：<script src="/a.js?v={{ STATIC_VERSION }}"></script>
# mako 模板中：<script src="/a.js?v=${ STATIC_VERSION }"></script>
# 如果静态资源修改了以后，上线前改这个版本号即可
#
STATIC_VERSION = "1.0"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]  # noqa

# CELERY 开关，使用时请改为 True，修改项目目录下的 Procfile 文件，添加以下两行命令：
# worker: python manage.py celery worker -l info
# beat: python manage.py celery beat -l info
# 不使用时，请修改为 False，并删除项目目录下的 Procfile 文件中 celery 配置
IS_USE_CELERY = False

# CELERY 并发数，默认为 2，可以通过环境变量或者 Procfile 设置
CELERYD_CONCURRENCY = os.getenv("BK_CELERYD_CONCURRENCY", 2)

# CELERY 配置，申明任务的文件路径，即包含有 @task 装饰器的函数文件
CELERY_IMPORTS = ()

# load logging settings
LOGGING = get_logging_config_dict(locals())

# 初始化管理员列表，列表中的人员将拥有预发布环境和正式环境的管理员权限
# 注意：请在首次提测和上线前修改，之后的修改将不会生效
INIT_SUPERUSER = [
    os.getenv("BK_INIT_SUPERUSER") or "admin",
]

# 使用mako模板时，默认打开的过滤器：h(过滤html)
MAKO_DEFAULT_FILTERS = ["h"]

# BKUI是否使用了history模式
IS_BKUI_HISTORY_MODE = False

# 是否需要对AJAX弹窗登录强行打开
IS_AJAX_PLAIN_MODE = False

# 国际化配置
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)  # noqa

TIME_ZONE = "Asia/Shanghai"
LANGUAGE_CODE = "zh-hans"

LANGUAGES = (
    ("en", u"English"),
    ("zh-hans", u"简体中文"),
)

"""
以下为框架代码 请勿修改
"""
# celery settings
if IS_USE_CELERY:
    INSTALLED_APPS = locals().get("INSTALLED_APPS", [])
    INSTALLED_APPS += ("django_celery_beat", "django_celery_results")
    CELERY_ENABLE_UTC = False
    CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

# remove disabled apps
if locals().get("DISABLED_APPS"):
    INSTALLED_APPS = locals().get("INSTALLED_APPS", [])
    DISABLED_APPS = locals().get("DISABLED_APPS", [])

    INSTALLED_APPS = [_app for _app in INSTALLED_APPS if _app not in DISABLED_APPS]

    _keys = (
        "AUTHENTICATION_BACKENDS",
        "DATABASE_ROUTERS",
        "FILE_UPLOAD_HANDLERS",
        "MIDDLEWARE",
        "PASSWORD_HASHERS",
        "TEMPLATE_LOADERS",
        "STATICFILES_FINDERS",
        "TEMPLATE_CONTEXT_PROCESSORS",
    )

    import itertools

    for _app, _key in itertools.product(DISABLED_APPS, _keys):
        if locals().get(_key) is None:
            continue
        locals()[_key] = tuple([_item for _item in locals()[_key] if not _item.startswith(_app + ".")])

ROOT_URLCONF = "bk_plugin_runtime.urls"

from blueapps.core.celery import celery_app  # noqa
from bk_plugin_framework.runtime.schedule.celery.beat import SCHEDULE  # noqa

celery_app.conf.beat_schedule = SCHEDULE


def logging_addition_settings(logging_dict):
    # apigw manager log setting
    logging_dict["loggers"]["apigw_manager"] = {
        "handlers": ["root"],
        "level": "INFO",
        "propagate": True,
    }

    logging_dict["loggers"]["bk_plugin"] = {
        "handlers": ["root"],
        "level": "INFO",
        "propagate": True,
    }
    if BKPAAS_ENVIRONMENT == "dev":
        # bk plugin log setting
        logging_dict["handlers"]["db_log_handler"] = {
            "class": "bk_plugin_framework.runtime.loghub.log.TraceContextLogHandler",
            "formatter": "simple",
        }
        logging_dict["loggers"]["bk_plugin"]["handlers"].append("db_log_handler")

        logging_dict["handlers"]["console"] = {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
        logging_dict["loggers"]["bk_plugin"]["handlers"].append("console")

    logging_dict.update(
        {"filters": {"trace_id_inject_filter": {"()": "bk_plugin_framework.utils.log.TraceIDInjectFilter"}}}
    )
    for _, handler in logging_dict["handlers"].items():
        handler.update({"filters": ["trace_id_inject_filter"]})
    format_keywords = ["format", "fmt"]
    for kw in format_keywords:
        if kw in logging_dict["formatters"]["verbose"]:
            logging_dict["formatters"]["verbose"].update(
                {"format": logging_dict["formatters"]["verbose"][kw].strip() + " [trace_id]: %(trace_id)s"}
            )
            break


# BK SOPS RELATE
BK_SOPS_APP_CODE = os.getenv("BK_SOPS_APP_CODE")

# ESB SDK
ESB_SDK_NAME = (
    "bk_plugin_runtime.packages.open.blueking.component"
    if os.getenv("BKPAAS_ENGINE_REGION", "open") != "ieod"
    else None
)

# APIGW MANAGER
BK_APP_CODE = os.getenv("BKPAAS_APP_ID")
BK_APP_SECRET = os.getenv("BKPAAS_APP_SECRET")
BK_APIGW_NAME = os.getenv("BKPAAS_BK_PLUGIN_APIGW_NAME")
# 兼容旧版环境变量 & PaaS V3 默认注入变量
BK_API_URL_TMPL = (
    os.getenv("BK_APIGW_MANAGER_URL_TMPL") or os.getenv("BK_APIGW_MANAGER_URL_TEMPL") or os.getenv("BK_API_URL_TMPL")
)
BK_PLUGIN_APIGW_STAGE_NAME = BKPAAS_ENVIRONMENT

BK_PLUGIN_APIGW_BACKEND_HOST = json.loads(os.getenv("BKPAAS_DEFAULT_PREALLOCATED_URLS", "{}")).get(
    BKPAAS_ENVIRONMENT, ""
)
url_parse = urllib.parse.urlparse(BK_PLUGIN_APIGW_BACKEND_HOST)
BK_PLUGIN_APIGW_BACKEND_NETLOC = url_parse.netloc
BK_PLUGIN_APIGW_BACKEND_SUB_PATH = url_parse.path.lstrip("/")
BK_PLUGIN_APIGW_BACKEND_SCHEME = url_parse.scheme or "http"

BK_APIGW_CORS_ALLOW_ORIGINS = os.getenv("BK_APIGW_CORS_ALLOW_ORIGINS", "")
BK_APIGW_CORS_ALLOW_METHODS = os.getenv("BK_APIGW_CORS_ALLOW_METHODS", "")
BK_APIGW_CORS_ALLOW_HEADERS = os.getenv("BK_APIGW_CORS_ALLOW_HEADERS", "")
BK_APIGW_DEFAULT_TIMEOUT = int(os.getenv("BK_APIGW_DEFAULT_TIMEOUT", "60"))
