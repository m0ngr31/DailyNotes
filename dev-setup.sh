#!/usr/bin/env bash

set -e  # Exit on error

echo "======================================"
echo "DailyNotes Development Setup"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
echo "Checking for Python..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed.${NC}"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

# Determine which Python command to use
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Check if pip is installed
echo "Checking for pip..."
if ! command -v $PIP_CMD &> /dev/null; then
    echo -e "${RED}Error: pip is not installed.${NC}"
    echo "Please install pip: https://pip.pypa.io/en/stable/installation/"
    exit 1
fi
echo -e "${GREEN}✓ Found pip${NC}"

# Check if Node.js is installed
echo "Checking for Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed.${NC}"
    echo "Please install Node.js >= 12 from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Found Node.js $NODE_VERSION${NC}"

# Check if npm is installed
echo "Checking for npm..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed.${NC}"
    echo "npm should come with Node.js. Please reinstall Node.js."
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ Found npm $NPM_VERSION${NC}"

echo ""
echo "======================================"
echo "Setting up Python Virtual Environment"
echo "======================================"
echo ""

# Create virtual environment if it doesn't exist
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists at $VENV_DIR${NC}"
else
    echo "Creating Python virtual environment..."
    if $PYTHON_CMD -m venv $VENV_DIR; then
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${RED}Error: Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""
echo "======================================"
echo "Installing Dependencies"
echo "======================================"
echo ""

# Install Python dependencies
echo "Installing Python dependencies from requirements.txt..."
if pip install -r requirements.txt; then
    echo -e "${GREEN}✓ Python dependencies installed successfully${NC}"
else
    echo -e "${RED}Error: Failed to install Python dependencies${NC}"
    exit 1
fi

echo ""

# Deactivate venv before installing Node dependencies to avoid Python path conflicts
deactivate

# Install Node dependencies
echo "Installing Node.js dependencies in client directory..."
if [ ! -d "client" ]; then
    echo -e "${RED}Error: client directory not found${NC}"
    exit 1
fi

cd client

# Remove old package-lock.json to force a fresh install with updated dependencies
if [ -f "package-lock.json" ]; then
    echo "Removing old package-lock.json..."
    rm package-lock.json
fi

# Remove node_modules if it exists to ensure clean install
if [ -d "node_modules" ]; then
    echo "Removing old node_modules..."
    rm -rf node_modules
fi

if npm install; then
    echo -e "${GREEN}✓ Node.js dependencies installed successfully${NC}"
else
    echo -e "${RED}Error: Failed to install Node.js dependencies${NC}"
    exit 1
fi
cd ..

# Reactivate venv for the environment setup step
echo "Reactivating virtual environment..."
source $VENV_DIR/bin/activate

echo ""
echo "======================================"
echo "Setting up Environment"
echo "======================================"
echo ""

# Run verify_env.py to create environment variables
echo "Generating environment configuration..."
if $PYTHON_CMD verify_env.py; then
    echo -e "${GREEN}✓ Environment configuration created${NC}"
    if [ -f "config/.env" ]; then
        echo -e "${YELLOW}Note: Environment variables saved to config/.env${NC}"
    fi
else
    echo -e "${RED}Error: Failed to create environment configuration${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo "Building Frontend"
echo "======================================"
echo ""

cd client
echo "Building Vue.js production bundle..."
if npm run build; then
    echo -e "${GREEN}✓ Frontend built successfully${NC}"
    echo "Built files available in dist/"
else
    echo -e "${YELLOW}Warning: Frontend build failed${NC}"
    echo "You can still run the development server with 'npm run serve'"
fi
cd ..

echo ""
echo "======================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "======================================"
echo ""
echo "You can now run the application:"
echo ""
echo -e "${BLUE}Option 1: Production Mode (Backend only, serves built frontend)${NC}"
echo "  ./run.sh"
echo "  Then visit: http://localhost:5001"
echo ""
echo -e "${BLUE}Option 2: Development Mode (Hot reload for frontend)${NC}"
echo "  Terminal 1 - Backend:"
echo "    ./run.sh"
echo ""
echo "  Terminal 2 - Frontend:"
echo "    cd client"
echo "    npm run serve"
echo "  Then visit: http://localhost:8080"
echo ""
echo -e "${YELLOW}Note: In development mode, run both servers simultaneously.${NC}"
echo ""
