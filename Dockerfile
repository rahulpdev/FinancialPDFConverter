# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Use the official uv image with Python 3.12 on bookworm-slim as the builder.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Configure uv for optimal Docker layer caching:
#   UV_COMPILE_BYTECODE  — pre-compile .pyc files (faster startup in runtime)
#   UV_LINK_MODE=copy    — copy files instead of hardlinks (required with cache mounts)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# ── Dependency layer (cached) ──────────────────────────────────────────────────
# Install production dependencies WITHOUT the project itself.
# Only re-runs when uv.lock or pyproject.toml change — keeps rebuilds fast.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# ── Project layer ──────────────────────────────────────────────────────────────
# Copy source and install the project itself as a non-editable package.
# --no-editable bakes the source into site-packages so runtime needs no src tree.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


# ── Stage 2: Runtime ───────────────────────────────────────────────────────────
# Lean runtime image — no uv, no build tools, no dev dependencies.
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Copy the virtual environment built in the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy application source (needed since entry points reference app/ package).
COPY --from=builder /app/main.py /app/main.py
COPY --from=builder /app/app /app/app

# Activate the virtual environment by prepending its bin/ to PATH.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8123

CMD ["python", "-m", "app.main"]
