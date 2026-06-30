ARG PYTHON_BASE_IMAGE=python:3.10.5-slim
FROM ${PYTHON_BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY template/{{cookiecutter.project_name}}/requirements.txt /tmp/bk-plugin-default-requirements.txt

RUN python --version \
    && python -m pip --version \
    && python -m pip install --no-cache-dir --upgrade pip==21.2.2 \
    && python -m pip --version \
    && python -m pip install --no-cache-dir -r /tmp/bk-plugin-default-requirements.txt \
    && python -c "import importlib.metadata as metadata; print('bk-plugin-framework', metadata.version('bk-plugin-framework')); print('bk-plugin-runtime', metadata.version('bk-plugin-runtime'))"
