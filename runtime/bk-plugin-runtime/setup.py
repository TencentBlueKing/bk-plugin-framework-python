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
with open(path.join(here, "bk_plugin_runtime", "__version__.py"), "r", encoding="utf-8") as f:
    exec(f.read(), about)

long_description = ""
version = about["__version__"]

setup(
    name="bk-plugin-runtime",
    version=version,
    description="bk-plugin-runtime",
    long_description=long_description,
    url="",
    author="Blueking",
    author_email="",
    include_package_data=True,
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "redis==2.10.5",
        "blueapps==3.3.6rc",
        "gunicorn==19.6.0",
        "djangorestframework==3.12.4",
        "drf-yasg==1.20.0",
        "raven==6.5.0",
        "ddtrace==0.14.1",
        "bk-plugin-framework>=1.0.0,<2.0.0",
        "celery==4.4.0",
        "Django==2.2.16,<3.0.0",
        "django-celery-beat==2.0.0",
        "django-celery-results==1.2.1",
        "django-cors-headers==3.8.0",
        "django-dbconn-retry==0.1.5",
    ],
    zip_safe=False,
)
