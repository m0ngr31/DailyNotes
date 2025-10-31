#!/usr/bin/env bash

set -e  # Exit on error

echo "======================================"
echo "DailyNotes Backend Server"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment exists
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    echo "Please run ./dev-setup.sh first to set up the development environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Load environment variables if .env exists
if [ -f "./config/.env" ]; then
    echo "Loading environment variables from config/.env..."
    . ./config/.env
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
fi

# Verify and generate environment configuration
echo ""
echo "Verifying environment configuration..."
if [ ! -f "./verify_env.py" ]; then
    echo -e "${RED}Error: verify_env.py not found${NC}"
    exit 1
fi

if python verify_env.py; then
    echo -e "${GREEN}✓ Environment configuration verified${NC}"
else
    echo -e "${RED}Error: Failed to verify environment configuration${NC}"
    exit 1
fi

# Reload environment variables after verification
if [ -f "./config/.env" ]; then
    . ./config/.env
fi

# Set Flask app
export FLASK_APP=server.py

# Check if server.py exists
if [ ! -f "./server.py" ]; then
    echo -e "${RED}Error: server.py not found${NC}"
    exit 1
fi

# Run database migrations
echo ""
echo "Running database migrations..."
if command -v flask &> /dev/null; then
    if flask db upgrade; then
        echo -e "${GREEN}✓ Database migrations completed${NC}"
    else
        echo -e "${RED}Error: Database migration failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: Flask command not found. Is Flask installed?${NC}"
    exit 1
fi

# Verify data migrations
echo ""
echo "Verifying data migrations..."
if [ ! -f "./verify_data_migrations.py" ]; then
    echo -e "${YELLOW}Warning: verify_data_migrations.py not found, skipping...${NC}"
else
    if python verify_data_migrations.py; then
        echo -e "${GREEN}✓ Data migrations verified${NC}"
    else
        echo -e "${RED}Error: Data migration verification failed${NC}"
        exit 1
    fi
fi

# Build frontend
echo ""
echo "======================================"
echo "Building Frontend"
echo "======================================"
echo ""

if [ ! -d "./client" ]; then
    echo -e "${RED}Error: client directory not found${NC}"
    exit 1
fi

cd client
echo "Building Vue.js production bundle..."
if npm run build; then
    echo -e "${GREEN}✓ Frontend built successfully${NC}"
else
    echo -e "${RED}Error: Frontend build failed${NC}"
    echo "You can still run the frontend development server separately:"
    echo "  cd client && npm run serve"
    exit 1
fi
cd ..

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo -e "${RED}Error: gunicorn not found. Is it installed?${NC}"
    exit 1
fi

# Start the server
echo ""
echo "======================================"
echo -e "${GREEN}Starting Gunicorn Server${NC}"
echo "======================================"
echo ""
echo -e "${BLUE}Server will be available at:${NC} http://0.0.0.0:5001"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

exec gunicorn server:app -b 0.0.0.0:5001
