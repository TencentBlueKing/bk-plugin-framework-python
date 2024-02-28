# -*- coding: utf-8 -*-
import logging

import jsonschema


logger = logging.getLogger("bk-plugin-framework")


ALLOW_SCOPE_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "value": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["type", "value"],
        },
    },
}


def validate_allow_scope(data: dict):
    try:
        jsonschema.validate(data, ALLOW_SCOPE_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        logger.exception(f"allow_scope is invalid: {e}")
        return False
    return True
