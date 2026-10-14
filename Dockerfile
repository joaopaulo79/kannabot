FROM python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 POETRY_NO_INTERACTION=1 POETRY_VIRTUALENVS_IN_PROJECT=true
WORKDIR /build
RUN pip install --no-cache-dir poetry==1.8.5
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-ansi
COPY src ./src
RUN poetry build --format wheel && .venv/bin/pip install --no-deps dist/*.whl

FROM python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d AS runtime
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.source="https://github.com/joaopaulo79/kannabot" org.opencontainers.image.revision=$SOURCE_REVISION
ENV PATH=/opt/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 KANNA_HOME=/state
COPY --from=build /build/.venv /opt/venv
RUN groupadd --gid 10001 kanna && useradd --uid 10001 --gid kanna --no-create-home kanna && mkdir -p /state/var /opt/kanna && chown -R kanna:kanna /state
WORKDIR /opt/kanna
COPY deploy ./deploy
USER 10001:10001
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD ["python", "-m", "deploy.healthcheck"]
ENTRYPOINT ["python", "-m", "deploy.runtime"]
