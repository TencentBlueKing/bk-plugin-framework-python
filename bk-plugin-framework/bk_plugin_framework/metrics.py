# -*- coding: utf-8 -*-
import os
import socket
import time
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge


def get_hostname():
    return socket.gethostname()


HOSTNAME = get_hostname()


def decode_buckets(buckets_list):
    return [float(x) for x in buckets_list.split(",")]


def get_histogram_buckets_from_env(env_name):
    if env_name in os.environ:
        buckets = decode_buckets(os.environ.get(env_name))
    else:
        buckets = (
            0.005,
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1.0,
            2.5,
            5.0,
            7.5,
            10.0,
            25.0,
            50.0,
            75.0,
            100.0,
            float("inf"),
        )
    return buckets


def setup_gauge(*gauges):
    def wrapper(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            plugin_cls = kwargs.get("plugin_cls")
            version = plugin_cls.Meta.version if plugin_cls else "unknown"
            for g in gauges:
                g.labels(hostname=HOSTNAME, version=version).inc(1)
            try:
                return func(*args, **kwargs)
            finally:
                for g in gauges:
                    g.labels(hostname=HOSTNAME, version=version).dec(1)

        return _wrapper

    return wrapper


def setup_histogram(*histograms):
    def wrapper(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            plugin_cls = kwargs.get("plugin_cls")
            version = plugin_cls.Meta.version if plugin_cls else "unknown"
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                for h in histograms:
                    h.labels(hostname=HOSTNAME, version=version).observe(time.perf_counter() - start)

        return _wrapper

    return wrapper


# 插件execute执行失败次数
BK_PLUGIN_EXECUTE_FAILED_COUNT = Counter(
    name="bk_plugin_execute_failed_count",
    documentation="count execute failed",
    labelnames=["version", "hostname"],
)

# 插件execute执行异常次数
BK_PLUGIN_EXECUTE_EXCEPTION_COUNT = Counter(
    name="bk_plugin_execute_exception_count",
    documentation="count execute exceptions",
    labelnames=["version", "hostname"],
)

# 插件schedule执行失败次数
BK_PLUGIN_SCHEDULE_FAILED_COUNT = Counter(
    name="bk_plugin_schedule_failed_count",
    documentation="count schdule failed",
    labelnames=["version", "hostname"],
)

# 插件schedule执行异常次数
BK_PLUGIN_SCHEDULE_EXCEPTION_COUNT = Counter(
    name="bk_plugin_schedule_exception_count",
    documentation="count schedule exceptions",
    labelnames=["version", "hostname"],
)

# 插件 execute 执行时间
BK_PLUGIN_EXECUTE_TIME = Histogram(
    name="bk_plugin_execute_time",
    documentation="time spent executing bk_plugin",
    buckets=get_histogram_buckets_from_env("BK_PLUGIN_METRICS_BUCKETS"),
    labelnames=["version", "hostname"],
)

# 插件 schedule 执行时间
BK_PLUGIN_SCHEDULE_TIME = Histogram(
    name="bk_plugin_schedule_time",
    documentation="time spent scheduling node",
    buckets=get_histogram_buckets_from_env("BAMBOO_ENGINE_METRICS_BUCKETS"),
    labelnames=["version", "hostname"],
)

# 正在执行的 EXECUTE 数量
BK_PLUGIN_EXECUTE_RUNNING_PROCESSES = Gauge(
    name="bk_plugin_execute_running_processes", documentation="count running state processes",
    labelnames=["hostname", "version"]
)

# 正在执行的 SCHEDULE 数量
BK_PLUGIN_SCHEDULE_RUNNING_PROCESSES = Gauge(
    name="bk_plugin_schedule_running_processes", documentation="count running state schedules",
    labelnames=["hostname", "version"]
)

# CALLBACK 异常次数
BK_PLUGIN_CALLBACK_EXCEPTION_COUNT = Counter(
    name="bk_plugin_callback_exception_count",
    documentation="count callback exception",
    labelnames=["version", "hostname"],
)

# CALLBACK 耗时计算
BK_PLUGIN_CALLBACK_TIME = Histogram(
    name="bk_plugin_callback_time",
    documentation="count callback time",
    buckets=get_histogram_buckets_from_env("BAMBOO_ENGINE_METRICS_BUCKETS"),
    labelnames=["version", "hostname"],
)
