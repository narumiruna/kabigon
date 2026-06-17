# https://docs.astral.sh/uv/guides/integration/docker/#non-editable-installs
ARG PYTHON_VERSION=3.12
ARG DEBIAN_VERSION=bookworm
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-${DEBIAN_VERSION}-slim AS uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --all-extras

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}

WORKDIR /app

COPY --from=uv --chown=app:app /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

ARG KABIGON_WITH_XVFB=0
ENV KABIGON_WITH_XVFB=${KABIGON_WITH_XVFB}
RUN playwright install --with-deps chromium \
    && if [ "$KABIGON_WITH_XVFB" = "1" ]; then \
        apt-get update \
        && apt-get install -y --no-install-recommends xauth xvfb \
        && rm -rf /var/lib/apt/lists/*; \
    fi

ENTRYPOINT ["sh", "-c", "if [ \"$KABIGON_WITH_XVFB\" = \"1\" ]; then exec xvfb-run -a kabigon \"$@\"; fi; exec kabigon \"$@\"", "--"]
