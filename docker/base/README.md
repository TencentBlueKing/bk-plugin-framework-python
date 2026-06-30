# BK Plugin Python Base Image

This directory contains the Dockerfile for the shared plugin Python base image. BK-CI should build this image from the repository root so the Docker build can copy the cookiecutter template requirements file.

## Tag Policy

The image tag must match the `bk-plugin-framework` version pinned in `template/{{cookiecutter.project_name}}/requirements.txt`.

For the current template:

```txt
bk-plugin-framework==2.3.14
bk-plugin-python-base:2.3.14
```

The Python patch version is not part of the image tag. Keep the upstream Python image aligned with `template/{{cookiecutter.project_name}}/runtime.txt`.

## BK-CI Build Command

Run the build from the repository root:

```bash
docker build \
  -f docker/base/Dockerfile \
  --build-arg PYTHON_BASE_IMAGE=<internal-python-3.10.5-image> \
  -t bk-plugin-python-base:2.3.14 \
  .
```

Push the image to the internal registry:

```bash
docker tag bk-plugin-python-base:2.3.14 <registry>/bk-plugin-python-base:2.3.14
docker push <registry>/bk-plugin-python-base:2.3.14
```

If the template should generate a full internal image path, set `base_image` in `template/cookiecutter.json` to the pushed image name, such as `<registry>/bk-plugin-python-base:2.3.14`.

## Verification

After building the image, verify the default framework and runtime packages are installed:

```bash
docker run --rm bk-plugin-python-base:2.3.14 python -c "import bk_plugin_framework, bk_plugin_runtime"
```

The command exits with status `0` when both packages are importable.
