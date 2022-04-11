"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# To use a consistent encoding
from codecs import open
from os import path

# Always prefer setuptools over distutils
from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))
about = {}
with open(path.join(here, "bk_plugin_framework", "__version__.py"), "r", encoding="utf-8") as f:
    exec(f.read(), about)

long_description = ""
version = about["__version__"]

setup(
    name="bk-plugin-framework",
    version=version,
    description="bk-plugin-framework",
    long_description=long_description,
    url="",
    author="Blueking",
    author_email="",
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        "pydantic>1.0,<2.0",
        "werkzeug>2.0.0,<3.0.0",
        "apigw-manager[extra]==0.1.9",
        "bk-plugin-runtime==1.1.0rc1"
    ],
    zip_safe=False,
)
