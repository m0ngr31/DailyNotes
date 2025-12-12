# ================================
# Stage 1: Frontend Builder
# ================================
FROM node:24-alpine AS frontend-builder

ARG APP_VERSION=dev

WORKDIR /app/client

# Copy package.json and postinstall script for better layer caching
COPY client/package.json client/patch-buefy.sh ./

# Install dependencies (postinstall runs patch-buefy.sh)
RUN npm install --prefer-offline --no-audit --legacy-peer-deps

# Copy client source and build
COPY client/ ./
RUN APP_VERSION=$APP_VERSION npm run build

# ================================
# Stage 2: Python Runtime
# ================================
FROM python:3.12-alpine

WORKDIR /app

# Install build dependencies, Python packages, then clean up in one layer
# Note: postgresql-libs and mariadb-connector-c are runtime deps for database drivers
COPY requirements.txt ./
RUN apk add --no-cache \
        postgresql-libs \
        mariadb-connector-c \
    && apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        postgresql-dev \
        mariadb-dev \
    && pip install --no-cache-dir \
        quart==0.20.0 \
        quart-cors==0.7.0 \
        alembic==1.14.0 \
        sqlalchemy[asyncio]==2.0.36 \
        aiosqlite==0.20.0 \
        uvicorn[standard]==0.34.0 \
        pyjwt==2.10.1 \
        argon2-cffi==23.1.0 \
        python-frontmatter==1.1.0 \
        pycryptodome==3.23.0 \
        httpx==0.28.1 \
        requests==2.32.5 \
        python-dateutil==2.9.0.post0 \
        psycopg2-binary==2.9.10 \
        asyncpg==0.30.0 \
        pymysql==1.1.1 \
        aiomysql==0.2.0 \
        cryptography>=44.0.1 \
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
