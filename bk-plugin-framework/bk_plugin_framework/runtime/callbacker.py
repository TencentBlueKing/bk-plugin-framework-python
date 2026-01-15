# -*- coding: utf-8 -*-
import json
import logging

import requests
from requests import HTTPError

logger = logging.getLogger("bk_plugin")


class PluginCallbacker:
    def __init__(self, callback_url, callback_data):
        self.callback_url = callback_url
        self.callback_data = callback_data

    @staticmethod
    def _check_response_with_result(json_response: dict):
        """当响应中没有 result 字段或 result 为 true 时，说明请求成功，否则说明请求失败"""
        if "result" in json_response and not json_response["result"]:
            return False
        return True

    def callback(self, *args, **kwargs):
        try:
            logger.info(f"[plugin callback]: url={self.callback_url}, data={self.callback_data}")
            response = requests.post(
                url=self.callback_url,
                data=json.dumps(self.callback_data),
                headers={"Content-Type": "application/json"},
                verify=False,
            )
            response.raise_for_status()
            if self._check_response_with_result(response.json()) is False:
                raise HTTPError(f"[plugin callback] response with result False: {response.json()}")
        except Exception as e:
            logger.exception(f"[plugin callback]: callback failed: {e}")
            raise

    def callback_with_retry(self, retry_times=3, *args, **kwargs):
        for i in range(retry_times):
            try:
                self.callback(*args, **kwargs)
            except Exception as e:
                logger.exception(f"[plugin callback with retry] callback {i+1} times failed: {e}")
            else:
                return
        logger.error(
            f"[plugin callback with retry] retry {retry_times} times "
            f"failed with {self.callback_url} and {self.callback_data}"
        )
