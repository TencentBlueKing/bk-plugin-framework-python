from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


def standard_response_enveloper(serializer_class, many: bool = False):
    """统一响应包装器"""
    component_name = "Enveloped{}{}".format(
        serializer_class.__name__.replace("Serializer", ""),
        "List" if many else "",
    )

    @extend_schema_serializer(many=False, component_name=component_name)
    class EnvelopeSerializer(serializers.Serializer):
        code = serializers.IntegerField(help_text="状态码，0表示成功")
        data = serializer_class(many=many)
        message = serializers.CharField(help_text="响应消息")
        result = serializers.BooleanField(help_text="操作结果")

    return EnvelopeSerializer
