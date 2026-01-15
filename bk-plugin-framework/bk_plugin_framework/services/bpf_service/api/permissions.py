# -*- coding: utf-8 -*-
from importlib import import_module

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from bk_plugin_framework.utils.validations import validate_allow_scope

try:
    meta_module = import_module("bk_plugin.meta")
except ImportError:
    allow_scope = {}
else:
    allow_scope = getattr(meta_module, "allow_scope", {})
    if validate_allow_scope(allow_scope) is False:
        raise RuntimeError("allow_scope in meta.py is invalid")


class ScopeAllowPermission(BasePermission):
    """
    业务域鉴权，仅支持通过 apigw 的请求
    """

    def has_permission(self, request: Request, view):
        if not allow_scope:
            return True

        bk_app_code = request.app.bk_app_code

        # 如果没有进行使用方配置，则默认放行，如果不希望放行在插件开发者中心配置即可
        if bk_app_code not in allow_scope:
            return True

        scope_type = request.headers.get("Bkplugin-Scope-Type")
        scope_value = request.headers.get("Bkplugin-Scope-Value")

        return scope_type == allow_scope[bk_app_code]["type"] and scope_value in allow_scope[bk_app_code]["value"]
