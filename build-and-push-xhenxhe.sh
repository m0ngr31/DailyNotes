#!/bin/bash

# Build and push script for xhenxhe/dailynotes Docker Hub repository
# This script builds the DailyNotes Docker image and pushes it to xhenxhe/dailynotes
#
# Usage:
#   ./build-and-push-xhenxhe.sh [version] [-y]
#
# If version is not provided, it will be read from client/package.json
# Use -y to skip confirmation prompt

set -e  # Exit on any error

# Parse arguments
AUTO_CONFIRM=false
VERSION_ARG=""

for arg in "$@"; do
    case $arg in
        -y|--yes)
            AUTO_CONFIRM=true
            shift
            ;;
        *)
            VERSION_ARG="$arg"
            shift
            ;;
    esac
done

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
if [ -n "$VERSION_ARG" ]; then
    VERSION="$VERSION_ARG"
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
echo -e "${YELLOW}Platforms: linux/amd64, linux/arm64${NC}"
echo ""

# Confirm before proceeding
if [ "$AUTO_CONFIRM" = false ]; then
    read -p "Continue with build and push? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Build cancelled.${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}Auto-confirm enabled, proceeding with build...${NC}"
fi

echo ""
echo -e "${GREEN}Step 1/4: Setting up buildx for multi-platform builds...${NC}"
docker buildx create --name dailynotes-builder --use 2>/dev/null || docker buildx use dailynotes-builder

echo ""
echo -e "${GREEN}Step 2/4: Building and pushing multi-platform Docker image...${NC}"
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "${DOCKER_IMAGE}:${VERSION}" \
  -t "${DOCKER_IMAGE}:latest" \
  --push \
  .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build and push failed${NC}"
    echo -e "${YELLOW}Note: Make sure you're logged in to Docker Hub${NC}"
    echo -e "${YELLOW}Run: docker login${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 3/4: Verifying images were pushed...${NC}"
docker buildx imagetools inspect "${DOCKER_IMAGE}:${VERSION}"

echo ""
echo -e "${GREEN}Step 4/4: Cleaning up builder...${NC}"
echo -e "${YELLOW}(Builder instance kept for future builds)${NC}"

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
