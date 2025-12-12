#!/bin/sh

if test -f "./config/.env"; then
  . ./config/.env
fi

./verify_env.py

if test -f "./config/.env"; then
  . ./config/.env
fi

# Run database migrations using Alembic
alembic -c migrations/alembic.ini upgrade head

./verify_data_migrations.py

# Use uvicorn ASGI server for async support
# --timeout-keep-alive 0 disables keep-alive timeout for idle HTTP connections
# Note: SSE streams remain open as long as the server yields data
exec uvicorn server:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 0
