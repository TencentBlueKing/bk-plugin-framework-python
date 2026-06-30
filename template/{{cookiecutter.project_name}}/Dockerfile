FROM {{cookiecutter.base_image}}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY custom_requirements.txt /app/custom_requirements.txt
RUN python -m pip install --no-cache-dir -r /app/custom_requirements.txt

COPY . /app
