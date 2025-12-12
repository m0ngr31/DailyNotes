# syntax=docker/dockerfile:1.4
# ================================
# Stage 1: Frontend Builder
# ================================
FROM node:24-alpine AS frontend-builder

ARG APP_VERSION=dev

WORKDIR /app/client

# Copy package files for better layer caching
COPY client/package.json client/package-lock.json* client/patch-buefy.sh ./

# Install dependencies with BuildKit cache mount for npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit --legacy-peer-deps 2>/dev/null || \
    npm install --prefer-offline --no-audit --legacy-peer-deps

# Copy client source and build
COPY client/ ./
RUN APP_VERSION=$APP_VERSION npm run build

# ================================
# Stage 2: Python Runtime
# ================================
FROM python:3.12-alpine

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt ./

# Install build dependencies, Python packages, then clean up in one layer
# Using BuildKit cache mount for pip to speed up rebuilds
RUN --mount=type=cache,target=/root/.cache/pip \
    apk add --no-cache \
        postgresql-libs \
        mariadb-connector-c \
    && apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        postgresql-dev \
        mariadb-dev \
    && pip install --no-cache-dir -r requirements.txt \
        --only-binary :all: 2>/dev/null || \
       pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy application files
COPY server.py config.py run.sh verify_env.py verify_data_migrations.py ./
COPY app ./app
COPY migrations ./migrations

# Copy built frontend from builder stage (Vue outputs to ../dist from client/)
COPY --from=frontend-builder /app/dist ./dist

# Make scripts executable and create config directory
RUN chmod +x run.sh verify_env.py verify_data_migrations.py \
    && mkdir -p /app/config

# Install curl for healthcheck (small footprint on Alpine)
RUN apk add --no-cache curl

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./run.sh"]
