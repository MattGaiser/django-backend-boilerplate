#!/bin/bash

# run-tests-simple.sh
# Simplified test runner that only starts essential services for faster testing
# 
# This script runs tests with minimal dependencies for quick feedback during development.
#
# Usage:
#   ./run-tests-simple.sh [--verbose]

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--verbose] [--help]"
            echo ""
            echo "Simplified test runner with minimal dependencies."
            echo ""
            echo "Options:"
            echo "  --verbose   Show detailed test output"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_step() {
    print_status "$BLUE" "🔄 $1"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

# Set required environment variables
export POSTGRES_DB=django_test_db
export DJANGO_ENV=test
export DEBUG=false
export SECRET_KEY='django-insecure-test-2%l-xabc_5q%*ch4c+_s4z12)fopd!cl2(h$6t(hj24glyd)nk'
export ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,django
export USE_GCS_EMULATOR=true
export GCS_EMULATOR_HOST=http://fake-gcs-server:9090
export GCS_BUCKET_NAME=test-bucket

echo "=========================================="
print_status "$BLUE" "🚀 Quick Test Runner (Essential Services Only)"
echo "=========================================="

print_step "Starting minimal test environment..."

# Create minimal compose override
cat > docker-compose.minimal-test.yml <<EOF
services:
  db:
    env_file:
      - .env.test
    volumes: 
      - type: tmpfs
        target: /var/lib/postgresql/data

  django:
    env_file:
      - .env.test
    environment:
      - DEBUG=false
      - POSTGRES_DB=django_test_db
      - POSTGRES_USER=django_test_user
      - POSTGRES_PASSWORD=django_test_password
      - POSTGRES_HOST=db
    depends_on:
      db:
        condition: service_healthy
      fake-gcs-server:
        condition: service_started
    command: >
      sh -c "python manage.py migrate &&
             pytest -v --tb=short --reuse-db"

  fake-gcs-server:
    command: -scheme http -host 0.0.0.0 -port 9090
EOF

# Clean up function
cleanup() {
    print_step "Cleaning up containers..."
    docker compose -f docker-compose.yml -f docker-compose.minimal-test.yml down --volumes --remove-orphans --timeout 10 >/dev/null 2>&1 || true
    rm -f docker-compose.minimal-test.yml
}

trap cleanup EXIT

# Run tests
if [ "$VERBOSE" = true ]; then
    print_step "Running tests with verbose output..."
    if docker compose -f docker-compose.yml -f docker-compose.minimal-test.yml run --rm django; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Tests failed"
        exit 1
    fi
else
    print_step "Running tests..."
    if docker compose -f docker-compose.yml -f docker-compose.minimal-test.yml run --rm django >/dev/null 2>&1; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Tests failed - run with --verbose to see details"
        exit 1
    fi
fi