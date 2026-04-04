FROM python:3.12-slim

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/worker

RUN groupadd --system --gid ${APP_GID} worker \
    && useradd --system --uid ${APP_UID} --gid ${APP_GID} --create-home --home-dir ${HOME} worker

WORKDIR /app

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY --chown=worker:worker . .

RUN mkdir -p /tmp/pelatnas-competition \
    && chown -R worker:worker /app /tmp/pelatnas-competition ${HOME}

USER worker
