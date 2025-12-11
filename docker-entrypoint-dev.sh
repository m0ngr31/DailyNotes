#!/bin/bash

# Development entrypoint script
# Starts both Flask backend and Vue frontend dev servers

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

# Set Flask environment variables for development
export FLASK_APP=server.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run database migrations
echo "🗄️  Running database migrations..."
flask db upgrade

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

# Start Flask backend with auto-reload
echo "🐍 Starting Flask backend on port 5001 (with auto-reload)..."
flask run --host=0.0.0.0 --port=5001 --reload &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Start Vue frontend dev server
echo "⚡ Starting Vue.js frontend dev server on port 8080..."
cd client
npm run serve -- --port 8080 --host 0.0.0.0 &
VUE_PID=$!

cd ..

echo ""
echo "✅ Development environment is ready!"
echo "   - Backend:  http://localhost:5001"
echo "   - Frontend: http://localhost:8080"
echo "   - API proxy configured in Vue dev server"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
