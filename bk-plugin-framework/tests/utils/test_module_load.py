import os
from importlib import import_module


def test_load_form_module_path():
    plugin_module = import_module("bk_plugin")
    forms_path = os.path.join(os.path.abspath(plugin_module.__file__).rsplit(os.sep, 1)[0], "forms")
    assert os.path.isdir(forms_path)
