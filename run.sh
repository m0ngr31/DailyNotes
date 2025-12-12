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
# --timeout-keep-alive 0 keeps SSE connections alive indefinitely
# --loop asyncio for compatibility with quart-flask-patch
exec uvicorn server:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 0 --loop asyncio
