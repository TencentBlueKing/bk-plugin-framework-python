import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = ROOT / "template"
PLUGIN_TEMPLATE_ROOT = TEMPLATE_ROOT / "{{cookiecutter.project_name}}"
COOKIECUTTER_JSON = TEMPLATE_ROOT / "cookiecutter.json"
TEMPLATE_REQUIREMENTS = PLUGIN_TEMPLATE_ROOT / "requirements.txt"
TEMPLATE_DOCKERFILE = PLUGIN_TEMPLATE_ROOT / "Dockerfile"
CUSTOM_REQUIREMENTS = PLUGIN_TEMPLATE_ROOT / "custom_requirements.txt"
BASE_DOCKERFILE = ROOT / "docker" / "base" / "Dockerfile"
BASE_README = ROOT / "docker" / "base" / "README.md"


def read_text(path):
    return path.read_text(encoding="utf-8")


def load_cookiecutter_config():
    return json.loads(read_text(COOKIECUTTER_JSON))


def get_framework_version():
    requirements = read_text(TEMPLATE_REQUIREMENTS)
    match = re.search(r"^bk-plugin-framework==([^\s#]+)$", requirements, re.MULTILINE)
    assert match, "template requirements.txt must pin bk-plugin-framework with =="
    return match.group(1)


def get_base_image_tag(base_image):
    assert ":" in base_image, "base_image must include a fixed tag"
    return base_image.rsplit(":", 1)[1]


def test_cookiecutter_base_image_matches_framework_version():
    config = load_cookiecutter_config()

    assert "base_image" in config
    assert config["base_image"].split("/")[-1].startswith("bk-plugin-python-base:")
    assert get_base_image_tag(config["base_image"]) == get_framework_version()


def test_template_dockerfile_uses_base_image_and_custom_requirements_only():
    dockerfile = read_text(TEMPLATE_DOCKERFILE)

    assert "FROM {{cookiecutter.base_image}}" in dockerfile
    assert "COPY custom_requirements.txt /app/custom_requirements.txt" in dockerfile
    assert "python -m pip install --no-cache-dir -r /app/custom_requirements.txt" in dockerfile
    assert "requirements.txt" not in dockerfile


def test_custom_requirements_contains_no_default_dependencies():
    custom_requirements = read_text(CUSTOM_REQUIREMENTS)

    assert "bk-plugin-framework" not in custom_requirements
    assert "opentelemetry-" not in custom_requirements
    assert "celery-prometheus-exporter" not in custom_requirements


def test_base_dockerfile_installs_template_requirements_from_repo_root():
    dockerfile = read_text(BASE_DOCKERFILE)

    assert "ARG PYTHON_BASE_IMAGE=python:3.10.5-slim" in dockerfile
    assert "FROM ${PYTHON_BASE_IMAGE}" in dockerfile
    assert "COPY template/{{cookiecutter.project_name}}/requirements.txt /tmp/bk-plugin-default-requirements.txt" in dockerfile
    assert "python -m pip install --no-cache-dir -r /tmp/bk-plugin-default-requirements.txt" in dockerfile
    assert "importlib.metadata" in dockerfile
    assert "bk-plugin-framework" in dockerfile
    assert "bk-plugin-runtime" in dockerfile


def test_base_image_readme_documents_bk_ci_build_command():
    readme = read_text(BASE_README)

    assert "docker build \\" in readme
    assert "-f docker/base/Dockerfile" in readme
    assert "--build-arg PYTHON_BASE_IMAGE=" in readme
    assert "-t bk-plugin-python-base:2.3.14" in readme
    assert "docker push <registry>/bk-plugin-python-base:2.3.14" in readme
