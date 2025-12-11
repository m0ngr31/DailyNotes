# ================================
# Stage 1: Builder
# ================================
FROM nikolaik/python-nodejs:python3.10-nodejs24 AS builder

# Version passed from CI
ARG APP_VERSION=dev

# Install build dependencies
RUN apt-get update && \
    apt-get install -y build-essential libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all source code first (node_modules excluded via .dockerignore)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node dependencies (regenerate lock file to avoid version mismatch)
RUN cd client && npm install --prefer-offline --no-audit --legacy-peer-deps

# Build frontend with version (creates /app/dist/)
RUN cd client && APP_VERSION=$APP_VERSION npm run build

# ================================
# Stage 2: Runtime
# ================================
FROM python:3.10-slim

# Install only runtime dependencies (no build tools needed)
RUN apt-get update && \
    apt-get install -y libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files from builder
COPY --from=builder /app/server.py .
COPY --from=builder /app/config.py .
COPY --from=builder /app/requirements.txt .
COPY --from=builder /app/run.sh .
COPY --from=builder /app/verify_env.py .
COPY --from=builder /app/verify_data_migrations.py .

# Copy Python application code
COPY --from=builder /app/app ./app
COPY --from=builder /app/migrations ./migrations

# Copy built frontend (static files only, no node_modules!)
COPY --from=builder /app/dist ./dist

# Make scripts executable
RUN chmod +x run.sh verify_env.py verify_data_migrations.py

# Create config directory
RUN mkdir -p /app/config

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./run.sh"]
