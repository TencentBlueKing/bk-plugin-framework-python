from bk_plugin_framework.utils.validations import validate_allow_scope


def test_validate_allow_scope():
    test_cases = [
        ({}, True),
        ({}, True),
        ({"system1": {"type": "project_id", "value": ["1", "2"]}}, True),
        ({"system1": {"type": "project_id", "value": []}}, True),
        ({"system1": {"type": "project_id", "value": ["2"]}}, True),
        ({"system1": {"type": "project_id"}}, False),
        ({"system1": {"type": "project_id", "value": "2"}}, False),
        ({"system1": {}}, False),
    ]

    for data, expected in test_cases:
        assert validate_allow_scope(data) == expected
