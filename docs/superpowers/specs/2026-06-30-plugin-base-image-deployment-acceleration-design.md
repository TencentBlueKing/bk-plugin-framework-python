# Plugin Base Image Deployment Acceleration Design

## Purpose

Plugin deployment is slow because every generated plugin project installs the full default dependency set during deployment. Most plugins do not need custom dependencies, so each deployment repeats the same dependency resolution and package installation work.

This design adds a reusable Python base image for the default plugin environment and updates the cookiecutter template to build plugin images incrementally. The repository provides the base image Dockerfile and template Dockerfile. The base image is built and published by an external BK-CI pipeline.

## Goals

- Build a base image that contains the default plugin runtime dependencies.
- Keep `template/{{cookiecutter.project_name}}/requirements.txt` as the single source of default Python dependencies.
- Preserve compatibility with existing non-Docker deployment flows that install `requirements.txt` directly.
- Add a generated plugin Dockerfile that uses the base image and only installs user custom dependencies.
- Use fixed base image tags aligned with the `bk-plugin-framework` version, such as `bk-plugin-python-base:2.3.14`.
- Allow BK-CI to override the upstream Python image through a build argument.

## Non-Goals

- This change does not add GitHub Actions or BK-CI pipeline configuration for publishing the image.
- This change does not redesign `app_desc.yml` process commands.
- This change does not introduce a new dependency lock system.
- This change does not remove or shrink the existing template `requirements.txt`.

## Decisions

The selected approach is to reuse `template/{{cookiecutter.project_name}}/requirements.txt` when building the base image. The template keeps that file unchanged for old deployment flows, while Docker-based plugin builds install only `custom_requirements.txt`.

The base image tag matches the framework version, not the Python version. For example, when the template pins `bk-plugin-framework==2.3.14`, the matching base image is `bk-plugin-python-base:2.3.14`. Users normally do not need to know the Python patch version. The Python version remains an internal base image implementation detail and should stay aligned with `runtime.txt`.

The base image Dockerfile starts from:

```dockerfile
ARG PYTHON_BASE_IMAGE=python:3.10.5-slim
FROM ${PYTHON_BASE_IMAGE}
```

BK-CI can pass an internal Python image with `--build-arg PYTHON_BASE_IMAGE=...`.

## File Structure

Add these files:

```txt
docker/base/Dockerfile
docker/base/README.md
template/{{cookiecutter.project_name}}/Dockerfile
template/{{cookiecutter.project_name}}/custom_requirements.txt
```

Update `template/cookiecutter.json` with a `base_image` parameter. Its default value should be the fixed base image tag for the template's current framework version, for example:

```json
"base_image": "bk-plugin-python-base:2.3.14"
```

## Base Image Design

`docker/base/Dockerfile` uses the repository root as the Docker build context. It copies `template/{{cookiecutter.project_name}}/requirements.txt` into the image and installs it during the base image build.

The base image should set predictable Python runtime defaults:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

It should also print useful build diagnostics, including Python version, pip version, and the installed `bk-plugin-framework` version. This keeps BK-CI failure logs easy to inspect when dependency resolution, package indexes, or upstream image changes break the build.

## Template Image Design

The generated plugin `Dockerfile` uses:

```dockerfile
FROM {{cookiecutter.base_image}}
```

It copies the plugin project into a stable working directory, installs `custom_requirements.txt`, and leaves process startup to `app_desc.yml`.

`custom_requirements.txt` is present by default and contains comments only. Users add custom third-party dependencies there when needed. The default plugin path should not reinstall `requirements.txt`, because those dependencies are already in the base image.

The existing `requirements.txt` remains part of the template and keeps the full default dependency list. It has two jobs:

1. It supports existing non-Docker deployment flows.
2. It is the dependency source for the base image.

## Build Flow

For a framework version such as `2.3.14`, BK-CI should build from the repository root:

```bash
docker build \
  -f docker/base/Dockerfile \
  --build-arg PYTHON_BASE_IMAGE=<internal-python-3.10.5-image> \
  -t bk-plugin-python-base:2.3.14 \
  .
```

Then BK-CI pushes the image to the internal registry:

```bash
docker tag bk-plugin-python-base:2.3.14 <registry>/bk-plugin-python-base:2.3.14
docker push <registry>/bk-plugin-python-base:2.3.14
```

The published tag must match the `bk-plugin-framework` pin in the template `requirements.txt`.

## Plugin Build Flow

Users generate a plugin project from the cookiecutter template. The generated Dockerfile references the fixed base image through `{{cookiecutter.base_image}}`.

Most users leave `custom_requirements.txt` unchanged. Their image build only copies plugin code and runs an empty custom dependency install step. Users with extra dependencies add them to `custom_requirements.txt`; conflicts then fail in the plugin image build instead of affecting the shared base image.

The existing `app_desc.yml` commands continue to run:

- `gunicorn bk_plugin_runtime.wsgi ...`
- `celery -A blueapps.core.celery worker ...`
- `celery -A blueapps.core.celery beat ...`
- `celery-prometheus-exporter ...`

## Error Handling

Base image build failures should expose enough log context to identify whether the failure comes from the upstream Python image, pip, package indexes, or dependency resolution. The base image build should fail fast when default dependencies cannot be installed.

Plugin image build failures caused by `custom_requirements.txt` remain local to that plugin. This preserves a fast and stable default path while still allowing plugin-specific dependencies.

If the framework version in template `requirements.txt` changes, the base image tag in `template/cookiecutter.json` must be updated to the same version. The implementation should include a lightweight validation test for this rule.

## Testing And Acceptance

Static checks:

- `docker/base/Dockerfile` builds from the repository root.
- `docker/base/Dockerfile` copies `template/{{cookiecutter.project_name}}/requirements.txt`.
- The generated template Dockerfile uses `{{cookiecutter.base_image}}`.
- `custom_requirements.txt` exists and contains no default third-party dependencies.
- The `bk-plugin-framework` version in template `requirements.txt` matches the tag in `template/cookiecutter.json` `base_image`.

Base image build check:

```bash
docker build -f docker/base/Dockerfile -t bk-plugin-python-base:2.3.14 .
docker run --rm bk-plugin-python-base:2.3.14 python -c "import bk_plugin_framework, bk_plugin_runtime"
```

Template image check:

1. Generate a plugin project with cookiecutter.
2. Build its Dockerfile with the fixed base image.
3. Confirm an empty `custom_requirements.txt` does not reinstall the full default dependency set.
4. Run `python bin/manage.py check` inside the image.
5. Add one lightweight custom dependency to `custom_requirements.txt` and confirm only the plugin image layer changes.

## Operational Notes

The base image should be published before templates reference the tag in normal user workflows. If the internal registry requires a full image name, set `base_image` in `cookiecutter.json` to the full registry path before releasing the template.

When releasing a new framework version, the expected order is:

1. Update template `requirements.txt` with the new `bk-plugin-framework` version.
2. Build and publish `bk-plugin-python-base:<framework-version>`.
3. Update template `base_image` to the matching fixed tag.
4. Verify a generated plugin project builds from that tag.
