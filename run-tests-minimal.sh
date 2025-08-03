#!/bin/bash

# run-tests-minimal.sh
# Minimal test runner that only starts essential services (Django + PostgreSQL)
# 
# This script runs tests with minimal dependencies for reliable and fast testing.
#
# Usage:
#   ./run-tests-minimal.sh [--verbose]

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
            echo "Minimal test runner with just Django + PostgreSQL."
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

# Clean up function
cleanup() {
    print_step "Cleaning up containers..."
    docker compose -f docker-compose.minimal-test.yml down --volumes --remove-orphans --timeout 10 >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "=========================================="
print_status "$BLUE" "🏃‍♂️ Minimal Test Runner (Django + PostgreSQL)"
echo "=========================================="

print_step "Starting minimal test environment..."

# Run tests
if [ "$VERBOSE" = true ]; then
    print_step "Running tests with verbose output..."
    if docker compose -f docker-compose.minimal-test.yml run --rm django; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Tests failed"
        exit 1
    fi
else
    print_step "Running tests..."
    if docker compose -f docker-compose.minimal-test.yml run --rm django >/dev/null 2>&1; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Tests failed - run with --verbose to see details"
        exit 1
    fi
fi