import drf_spectacular.openapi
import drf_spectacular.utils


class IgnoreExcludeAutoSchema(drf_spectacular.openapi.AutoSchema):
    """忽略 @extend_schema(exclude=True)，将所有 API 暴露到 Swagger 文档中"""

    def is_excluded(self) -> bool:
        return False


# Patch extend_schema 装饰器，使 exclude 参数无效
_original_extend_schema = drf_spectacular.utils.extend_schema


def _patched_extend_schema(*args, exclude=None, **kwargs):
    """将 exclude 强制设为 None，使 @extend_schema(exclude=True) 不生效"""
    return _original_extend_schema(*args, exclude=None, **kwargs)


drf_spectacular.utils.extend_schema = _patched_extend_schema
