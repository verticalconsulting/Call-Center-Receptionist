###############################################
# Base stage (shared between build and final) #
###############################################
FROM python:3.12-slim-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

############################
# Frontend build stage      #
############################
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build -- --outDir /tmp/booking-build

###############
# Build stage #
###############
FROM base AS builder

## Install and configure UV, see https://docs.astral.sh/uv/ for more information
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Create virtual environment explicitly
RUN python -m venv /app/.venv

# Upgrade pip in the virtual environment to fix security vulnerability GHSA-4xh5-x5gv-qwph
RUN /app/.venv/bin/pip install --upgrade pip

# Copy dependency files
COPY server/pyproject.toml server/uv.lock /app/

# Sync the project into a new environment, using the frozen lockfile
RUN uv sync --frozen --no-dev --no-install-project --no-editable --all-packages

COPY server/*.py server/*.md server/*.json /app/
COPY server/app /app/app/
COPY server/static /app/static/
COPY server/prompts /app/prompts/

# Copy frontend build output into static/booking
COPY --from=frontend-builder /tmp/booking-build /app/static/booking

###############
# Final image #
###############
FROM base

RUN groupadd -r app
RUN useradd -r -d /app -g app -N app

# Copy built app from builder stage and set ownership
COPY --from=builder --chown=app:app /app /app

WORKDIR /app

# Switch to non-root user
USER app

EXPOSE 8000
ENTRYPOINT ["/app/.venv/bin/python",  "server.py"]
