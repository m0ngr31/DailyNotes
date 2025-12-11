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
        flask==3.1.2 \
        flask_sqlalchemy==3.1.1 \
        flask-migrate==4.1.0 \
        gunicorn==23.0.0 \
        flask-jwt-extended==4.7.1 \
        flask-argon2==0.3.0.0 \
        python-frontmatter==1.1.0 \
        pycryptodome==3.23.0 \
        requests==2.32.5 \
        python-dateutil==2.9.0.post0 \
        psycopg2-binary==2.9.10 \
        pymysql==1.1.1 \
        cryptography==44.0.0 \
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
