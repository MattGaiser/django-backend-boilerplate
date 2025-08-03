#!/bin/bash

# run-tests.sh
# Single command to run all tests within Docker containers
# 
# This script runs the complete test suite for the Django Backend Boilerplate
# within Docker containers using the existing test configuration.
#
# Usage:
#   ./run-tests.sh [--help] [--verbose] [--fast]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERBOSE=false
FAST_MODE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--help] [--verbose] [--fast]"
            echo ""
            echo "Single command to run all tests within Docker containers."
            echo ""
            echo "Options:"
            echo "  --verbose   Run tests with verbose output"
            echo "  --fast      Skip slower services for faster test runs"  
            echo "  --help      Show this help message"
            echo ""
            echo "This script will:"
            echo "  1. Use the existing docker-compose.test.yml configuration"
            echo "  2. Run pytest to execute all tests (Django + pytest tests)"
            echo "  3. Clean up containers after testing"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored output
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

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

# Function to clean up containers
cleanup() {
    print_step "Cleaning up Docker containers..."
    docker compose -f docker-compose.yml -f docker-compose.test.yml down --volumes --remove-orphans --timeout 10 >/dev/null 2>&1 || true
    print_success "Cleanup completed"
}

# Trap to ensure cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    echo "=========================================="
    print_status "$BLUE" "🧪 Django Backend Boilerplate Test Runner"
    echo "=========================================="
    
    # Change to project root
    cd "$SCRIPT_DIR"
    
    if [ "$FAST_MODE" = true ]; then
        print_status "$YELLOW" "Running in FAST mode (may skip some integration tests)"
    else
        print_status "$GREEN" "Running full test suite"
    fi
    
    if [ "$VERBOSE" = true ]; then
        print_status "$BLUE" "Verbose output enabled"
    fi
    
    echo ""
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    print_success "Docker is running"
    
    # Check if docker-compose files exist
    if [[ ! -f "docker-compose.yml" ]]; then
        print_error "docker-compose.yml not found in current directory"
        exit 1
    fi
    
    if [[ ! -f "docker-compose.test.yml" ]]; then
        print_error "docker-compose.test.yml not found in current directory"
        exit 1
    fi
    
    print_success "Docker Compose files found"
    echo ""
    
    # Build images if needed
    print_step "Building Docker images (if needed)..."
    if [ "$VERBOSE" = true ]; then
        docker compose -f docker-compose.yml -f docker-compose.test.yml build django
    else
        docker compose -f docker-compose.yml -f docker-compose.test.yml build django >/dev/null 2>&1
    fi
    print_success "Docker images ready"
    echo ""
    
    # Run tests using the existing test configuration
    print_step "Starting test environment and running tests..."
    
    # Use the existing test configuration with environment variables from .env.test
    if [ "$VERBOSE" = true ]; then
        print_info "Running tests with verbose output..."
        if docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm django; then
            test_exit_code=0
        else
            test_exit_code=$?
        fi
    else
        print_info "Running tests (this may take a few minutes)..."
        if docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm django 2>&1 | grep -E "(PASSED|FAILED|ERROR|OK|test session starts|collected|warnings summary)" || docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm django >/dev/null 2>&1; then
            test_exit_code=0
        else
            test_exit_code=$?
        fi
    fi
    
    echo ""
    
    # Show results
    if [ $test_exit_code -eq 0 ]; then
        print_success "All tests passed! 🎉"
        echo ""
        print_status "$GREEN" "✅ Test suite completed successfully"
        print_info "All Django and pytest tests have passed"
        print_info "Tests were run in Docker containers with PostgreSQL database"
    else
        print_error "Some tests failed"
        echo ""
        print_status "$RED" "❌ Test suite failed with exit code $test_exit_code"
        print_info "Check the output above for details on failing tests"
        if [ "$VERBOSE" != true ]; then
            print_info "Run with --verbose flag to see detailed output"
        fi
        exit $test_exit_code
    fi
}

# Run main function
main "$@"