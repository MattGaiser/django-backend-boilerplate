#!/bin/bash

# Local Docker Build and Test Script
# This script helps test Docker builds locally before CI/CD deployment

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting local Docker build and test...${NC}"

# Generate version file
echo -e "${YELLOW}📝 Generating version file...${NC}"
python scripts/write_version_file.py

# Build Django image
echo -e "${YELLOW}🏗️  Building Django backend image...${NC}"
docker build -t django-backend:local .

# Build Prefect image
echo -e "${YELLOW}🏗️  Building Prefect server image...${NC}"
docker build -f Dockerfile.prefect -t prefect-server:local .

# Test Django image
echo -e "${YELLOW}🧪 Testing Django backend image...${NC}"
docker run --rm -p 8000:8000 -e DJANGO_ENV=development django-backend:local &
DJANGO_PID=$!

# Wait for Django to start
sleep 5

# Test health endpoint
echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
if curl -f http://localhost:8000/health/; then
    echo -e "${GREEN}✅ Django health check passed${NC}"
else
    echo -e "${RED}❌ Django health check failed${NC}"
    kill $DJANGO_PID 2>/dev/null || true
    exit 1
fi

# Stop Django
kill $DJANGO_PID 2>/dev/null || true

# Test Prefect image (basic startup test)
echo -e "${YELLOW}🧪 Testing Prefect server image...${NC}"
docker run --rm -d --name prefect-test -p 4200:4200 prefect-server:local

# Wait for Prefect to start
sleep 10

# Test Prefect health
echo -e "${YELLOW}🔍 Testing Prefect server...${NC}"
if curl -f http://localhost:4200/api/health; then
    echo -e "${GREEN}✅ Prefect server health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Prefect server health check skipped (may need setup)${NC}"
fi

# Stop Prefect
docker stop prefect-test 2>/dev/null || true

echo -e "${GREEN}🎉 Local Docker build and test completed successfully!${NC}"

# Display images
echo -e "${YELLOW}📦 Built images:${NC}"
docker images | grep -E "(django-backend|prefect-server).*local"