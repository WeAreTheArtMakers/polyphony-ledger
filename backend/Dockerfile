# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY backend/pyproject.toml /build/backend/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    python -c "import pathlib,tomllib; data=tomllib.loads(pathlib.Path('/build/backend/pyproject.toml').read_text()); pathlib.Path('/build/requirements.txt').write_text('\\n'.join(data['project']['dependencies']) + '\\n')"

RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir /build/wheels -r /build/requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY --from=deps /build/wheels /wheels
COPY --from=deps /build/requirements.txt /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-index --find-links=/wheels -r /tmp/requirements.txt

COPY backend /app/backend
COPY proto /app/proto

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps /app/backend && \
    mkdir -p /app/backend/app/generated && \
    python -m grpc_tools.protoc -I /app/proto --python_out=/app/backend/app/generated \
      /app/proto/tx_raw.proto /app/proto/tx_validated.proto /app/proto/ledger_entry_batch.proto && \
    touch /app/backend/app/generated/__init__.py

WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
