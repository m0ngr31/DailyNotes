#!/bin/bash

# Build and push script for xhenxhe/dailynotes Docker Hub repository
# This script builds the DailyNotes Docker image and pushes it to xhenxhe/dailynotes
#
# Usage:
#   ./build-and-push-xhenxhe.sh [version]
#
# If version is not provided, it will be read from client/package.json

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Docker Hub username and repository
DOCKER_USERNAME="xhenxhe"
DOCKER_REPO="dailynotes"
DOCKER_IMAGE="${DOCKER_USERNAME}/${DOCKER_REPO}"

echo -e "${GREEN}=== DailyNotes Docker Build and Push ===${NC}"
echo -e "Target repository: ${YELLOW}${DOCKER_IMAGE}${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Get version from argument or package.json
if [ -n "$1" ]; then
    VERSION="$1"
    echo -e "${YELLOW}Using version from argument: ${VERSION}${NC}"
else
    if [ ! -f "client/package.json" ]; then
        echo -e "${RED}Error: client/package.json not found${NC}"
        exit 1
    fi

    VERSION=$(grep -o '"version": *"[^"]*"' client/package.json | sed 's/"version": *"\(.*\)"/\1/')

    if [ -z "$VERSION" ]; then
        echo -e "${RED}Error: Could not read version from client/package.json${NC}"
        exit 1
    fi

    echo -e "${GREEN}Version detected from package.json: ${VERSION}${NC}"
fi

echo ""
echo -e "${YELLOW}This will build and push the following tags:${NC}"
echo -e "  - ${DOCKER_IMAGE}:${VERSION}"
echo -e "  - ${DOCKER_IMAGE}:latest"
echo ""

# Confirm before proceeding
read -p "Continue with build and push? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Build cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1/4: Building Docker image...${NC}"
docker build -t "${DOCKER_IMAGE}:${VERSION}" -t "${DOCKER_IMAGE}:latest" .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 2/4: Checking Docker Hub login...${NC}"
if ! docker info | grep -q "Username: ${DOCKER_USERNAME}"; then
    echo -e "${YELLOW}Not logged in to Docker Hub. Attempting login...${NC}"
    docker login

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Docker login failed${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Step 3/4: Pushing ${DOCKER_IMAGE}:${VERSION}...${NC}"
docker push "${DOCKER_IMAGE}:${VERSION}"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to push versioned tag${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 4/4: Pushing ${DOCKER_IMAGE}:latest...${NC}"
docker push "${DOCKER_IMAGE}:latest"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to push latest tag${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Build and Push Complete ===${NC}"
echo ""
echo -e "Images pushed successfully:"
echo -e "  ✓ ${DOCKER_IMAGE}:${VERSION}"
echo -e "  ✓ ${DOCKER_IMAGE}:latest"
echo ""
echo -e "Users can now pull with:"
echo -e "  ${YELLOW}docker pull ${DOCKER_IMAGE}:${VERSION}${NC}"
echo -e "  ${YELLOW}docker pull ${DOCKER_IMAGE}:latest${NC}"
echo ""
