#!/bin/bash

# run-tests-direct.sh
# Direct test runner using just Django container with SQLite for faster testing
# 
# This script runs tests using SQLite instead of PostgreSQL for faster feedback

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
            echo "Direct test runner using SQLite for fast testing."
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

echo "=========================================="
print_status "$BLUE" "🏃‍♂️ Direct Test Runner (SQLite)"
echo "=========================================="

print_step "Building Django image..."

# Build the Django image
if [ "$VERBOSE" = true ]; then
    docker build -t django-test .
else
    docker build -t django-test . >/dev/null 2>&1
fi

print_success "Django image built"

print_step "Running tests in container..."

# Run tests directly in a container with SQLite
test_command="
cd /app &&
export DJANGO_SETTINGS_MODULE=DjangoBoilerplate.settings &&
export DJANGO_ENV=test &&
export DEBUG=false &&
export SECRET_KEY='django-insecure-test-key-for-testing' &&
export USE_POSTGRES=false &&
export DATABASE_URL=sqlite:////tmp/test_db.sqlite3 &&
python manage.py migrate &&
pytest -v --tb=short
"

if [ "$VERBOSE" = true ]; then
    if docker run --rm -v "$(pwd):/app" django-test sh -c "$test_command"; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Tests failed"
        exit 1
    fi
else
    if docker run --rm -v "$(pwd):/app" django-test sh -c "$test_command" >/dev/null 2>&1; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Tests failed - run with --verbose to see details"
        exit 1
    fi
fi