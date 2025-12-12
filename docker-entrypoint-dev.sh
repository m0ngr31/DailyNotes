#!/bin/bash

# Development entrypoint script
# Starts both Quart backend and Vue frontend dev servers

set -e

echo "🚀 Starting DailyNotes Development Environment..."

# Source environment variables if they exist
if [ -f "./config/.env" ]; then
  echo "📝 Loading environment variables from config/.env"
  set -a
  source ./config/.env
  set +a
fi

# Generate environment if needed
echo "🔧 Verifying environment configuration..."
./verify_env.py

# Source again after potential generation
if [ -f "./config/.env" ]; then
  set -a
  source ./config/.env
  set +a
fi

# Run database migrations using Alembic
echo "🗄️  Running database migrations..."
alembic -c migrations/alembic.ini upgrade head

# Run data migrations
echo "🔄 Running data migrations..."
./verify_data_migrations.py

# Function to handle shutdown
cleanup() {
  echo ""
  echo "🛑 Shutting down development servers..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}

trap cleanup SIGTERM SIGINT

# Start Quart backend with uvicorn (with auto-reload)
# Use --loop asyncio for compatibility with quart-flask-patch
echo "🐍 Starting Quart backend on port 8000 (with auto-reload)..."
uvicorn server:app --host 0.0.0.0 --port 8000 --reload --loop asyncio &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Vue frontend dev server
echo "⚡ Starting Vue.js frontend dev server on port 8080..."
cd client
npm run serve -- --port 8080 --host 0.0.0.0 &
VUE_PID=$!

cd ..

echo ""
echo "✅ Development environment is ready!"
echo "   - Backend:  http://localhost:8000"
echo "   - Frontend: http://localhost:8080"
echo "   - API proxy configured in Vue dev server"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
