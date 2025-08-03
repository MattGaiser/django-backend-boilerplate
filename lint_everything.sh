#!/bin/bash

# lint_everything.sh
# Comprehensive linting script for Django Backend Boilerplate
# 
# This script standardizes code formatting, import organization, and removes unused imports
# across the entire codebase using industry-standard Python linting tools.
#
# Usage:
#   ./lint_everything.sh [--check] [--help]
#
# Options:
#   --check     Run in check-only mode (don't modify files, just report issues)
#   --help      Show this help message
#
# Tools used:
#   - autoflake: Remove unused imports and variables
#   - isort:     Sort and organize imports  
#   - black:     Format code according to PEP 8
#   - flake8:    Check for style guide enforcement and code issues

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CHECK_ONLY=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Directories and files to exclude from linting
EXCLUDE_PATTERNS=(
    "--exclude=migrations"
    "--exclude=__pycache__"
    "--exclude=.git"
    "--exclude=node_modules"
    "--exclude=venv"
    "--exclude=env"
    "--exclude=.venv"
    "--exclude=.env"
    "--exclude=*.pyc"
    "--exclude=.idea"
    "--exclude=*.egg-info"
    "--exclude=dist"
    "--exclude=build"
)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--check] [--help]"
            echo ""
            echo "Comprehensive linting script for Django Backend Boilerplate"
            echo ""
            echo "Options:"
            echo "  --check     Run in check-only mode (don't modify files)"
            echo "  --help      Show this help message"
            echo ""
            echo "This script will:"
            echo "  1. Remove unused imports and variables (autoflake)"
            echo "  2. Sort and organize imports (isort)"
            echo "  3. Format code according to PEP 8 (black)"
            echo "  4. Check for style guide violations (flake8)"
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install missing dependencies
install_dependencies() {
    print_step "Checking and installing required dependencies..."
    
    local missing_tools=()
    
    if ! command_exists autoflake; then
        missing_tools+=("autoflake")
    fi
    
    if ! command_exists isort; then
        missing_tools+=("isort")
    fi
    
    if ! command_exists black; then
        missing_tools+=("black")
    fi
    
    if ! command_exists flake8; then
        missing_tools+=("flake8")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_warning "Missing tools: ${missing_tools[*]}"
        print_step "Installing missing dependencies from requirements-dev.txt..."
        pip install -r requirements-dev.txt
    else
        print_success "All required tools are available"
    fi
}

# Function to run autoflake
run_autoflake() {
    print_step "Running autoflake to remove unused imports and variables..."
    
    local autoflake_args=(
        "--remove-all-unused-imports"
        "--remove-unused-variables" 
        "--remove-duplicate-keys"
        "--recursive"
        "."
    )
    
    if [ "$CHECK_ONLY" = true ]; then
        autoflake_args+=("--check")
        print_step "Checking for unused imports (no changes will be made)..."
    else
        autoflake_args+=("--in-place")
        print_step "Removing unused imports and variables..."
    fi
    
    if autoflake "${autoflake_args[@]}"; then
        if [ "$CHECK_ONLY" = true ]; then
            print_success "No unused imports or variables found"
        else
            print_success "Unused imports and variables removed"
        fi
    else
        if [ "$CHECK_ONLY" = true ]; then
            print_warning "Found unused imports or variables"
            return 1
        else
            print_error "Error removing unused imports"
            return 1
        fi
    fi
}

# Function to run isort
run_isort() {
    print_step "Running isort to organize imports..."
    
    local isort_args=(
        "--profile=black"  # Compatible with black formatting
        "--multi-line=3"
        "--line-length=88"
        "--force-grid-wrap=0"
        "--use-parentheses"
        "--ensure-newline-before-comments"
        "."
    )
    
    if [ "$CHECK_ONLY" = true ]; then
        isort_args+=("--check-only" "--diff")
        print_step "Checking import organization (no changes will be made)..."
    else
        print_step "Organizing imports..."
    fi
    
    if isort "${isort_args[@]}"; then
        if [ "$CHECK_ONLY" = true ]; then
            print_success "All imports are properly organized"
        else
            print_success "Imports organized successfully"
        fi
    else
        if [ "$CHECK_ONLY" = true ]; then
            print_warning "Found incorrectly organized imports"
            return 1
        else
            print_error "Error organizing imports"
            return 1
        fi
    fi
}

# Function to run black
run_black() {
    print_step "Running black to format code..."
    
    local black_args=(
        "--line-length=88"
        "."
    )
    
    if [ "$CHECK_ONLY" = true ]; then
        black_args+=("--check" "--diff")
        print_step "Checking code formatting (no changes will be made)..."
    else
        print_step "Formatting code..."
    fi
    
    if black "${black_args[@]}"; then
        if [ "$CHECK_ONLY" = true ]; then
            print_success "All code is properly formatted"
        else
            print_success "Code formatted successfully"
        fi
    else
        if [ "$CHECK_ONLY" = true ]; then
            print_warning "Found code formatting issues"
            return 1
        else
            print_error "Error formatting code"
            return 1
        fi
    fi
}

# Function to run flake8
run_flake8() {
    print_step "Running flake8 to check for style violations..."
    
    local flake8_args=(
        "--max-line-length=88"
        "--extend-ignore=E203,W503"  # Ignore conflicts with black
        "--exclude=migrations,__pycache__,.git,node_modules,venv,env,.venv,.env,*.pyc,.idea,*.egg-info,dist,build"
        "."
    )
    
    if flake8 "${flake8_args[@]}"; then
        print_success "No style violations found"
    else
        print_warning "Found style violations (see output above)"
        return 1
    fi
}

# Function to show summary
show_summary() {
    local exit_code=$1
    echo ""
    echo "=========================================="
    print_step "LINTING SUMMARY"
    echo "=========================================="
    
    if [ "$CHECK_ONLY" = true ]; then
        if [ $exit_code -eq 0 ]; then
            print_success "All checks passed! Code is properly formatted and organized."
        else
            print_warning "Some checks failed. Run without --check to fix issues automatically."
        fi
    else
        if [ $exit_code -eq 0 ]; then
            print_success "All linting completed successfully!"
            print_status "$GREEN" "Your code is now:"
            echo "  ✅ Free of unused imports and variables"
            echo "  ✅ Properly import-organized"  
            echo "  ✅ Formatted according to PEP 8"
            echo "  ✅ Free of style violations"
        else
            print_error "Some linting steps failed. Please review the output above."
        fi
    fi
    
    echo ""
    print_status "$BLUE" "Tools used:"
    echo "  • autoflake: Remove unused imports and variables"
    echo "  • isort:     Sort and organize imports"
    echo "  • black:     Format code according to PEP 8"
    echo "  • flake8:    Check for style guide enforcement"
}

# Main execution
main() {
    echo "=========================================="
    print_status "$BLUE" "🚀 Django Backend Boilerplate Linter"
    echo "=========================================="
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    if [ "$CHECK_ONLY" = true ]; then
        print_status "$YELLOW" "Running in CHECK-ONLY mode (no files will be modified)"
    else
        print_status "$GREEN" "Running in FIX mode (files will be modified)"
    fi
    
    echo ""
    
    # Install dependencies if needed
    install_dependencies
    echo ""
    
    # Track overall success
    local overall_success=true
    
    # Run each linting step
    if ! run_autoflake; then
        overall_success=false
    fi
    echo ""
    
    if ! run_isort; then
        overall_success=false
    fi
    echo ""
    
    if ! run_black; then
        overall_success=false
    fi
    echo ""
    
    if ! run_flake8; then
        overall_success=false
    fi
    
    # Show summary
    if [ "$overall_success" = true ]; then
        show_summary 0
        exit 0
    else
        show_summary 1
        exit 1
    fi
}

# Run main function
main "$@"