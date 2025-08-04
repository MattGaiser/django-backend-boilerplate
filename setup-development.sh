#!/bin/bash

# setup-development.sh
# One-command setup for development environment with all enterprise features

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_NAME="${VENV_NAME:-venv}"

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

# Check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_success "Python $python_version found"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found - some features may not work"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_warning "Docker is installed but not running"
        return 1
    fi
    
    print_success "Docker is available and running"
    return 0
}

# Setup Python virtual environment
setup_virtual_env() {
    print_step "Setting up Python virtual environment"
    
    if [ ! -d "$VENV_NAME" ]; then
        python3 -m venv "$VENV_NAME"
        print_success "Created virtual environment: $VENV_NAME"
    else
        print_info "Virtual environment already exists: $VENV_NAME"
    fi
    
    # Activate virtual environment
    source "$VENV_NAME/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    print_success "Virtual environment activated and pip upgraded"
}

# Install Python dependencies
install_dependencies() {
    print_step "Installing Python dependencies"
    
    # Install production dependencies
    pip install -r requirements.txt
    print_success "Production dependencies installed"
    
    # Install development dependencies
    pip install -r requirements-dev.txt
    print_success "Development dependencies installed"
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_step "Setting up pre-commit hooks"
    
    # Initialize pre-commit
    pre-commit install
    
    # Initialize secrets baseline
    if [ ! -f ".secrets.baseline" ]; then
        detect-secrets scan --baseline .secrets.baseline
        print_success "Created secrets baseline"
    else
        print_info "Secrets baseline already exists"
    fi
    
    print_success "Pre-commit hooks installed"
    
    # Optionally run pre-commit on all files
    read -p "Run pre-commit checks on all files now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Running pre-commit on all files..."
        pre-commit run --all-files || true  # Don't fail if some checks fail
        print_info "Pre-commit run completed (some failures are normal on first run)"
    fi
}

# Setup mypy configuration
setup_mypy() {
    print_step "Setting up mypy configuration"
    
    cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.11
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
strict_optional = true

[mypy-django.*]
ignore_errors = true

[mypy-rest_framework.*]
ignore_errors = true

[mypy-allauth.*]
ignore_errors = true

[mypy-structlog.*]
ignore_errors = true

[mypy-prefect.*]
ignore_errors = true

[mypy-factory.*]
ignore_errors = true

[mypy-pytest.*]
ignore_errors = true

[mypy-psutil.*]
ignore_missing_imports = true

[mypy-redis.*]
ignore_missing_imports = true
EOF
    
    print_success "Created mypy configuration"
}

# Create development .env file
create_dev_env() {
    print_step "Creating development environment file"
    
    if [ ! -f ".env" ]; then
        cp .env.dev .env
        print_success "Created .env from .env.dev"
        print_warning "Remember to update .env with your specific configuration"
    else
        print_info ".env file already exists"
    fi
}

# Setup git hooks (additional to pre-commit)
setup_git_hooks() {
    print_step "Setting up additional git hooks"
    
    # Create commit-msg hook for conventional commits
    cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash
# Check for conventional commit format
if ! grep -qE '^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+' "$1"; then
    echo "Invalid commit message format!"
    echo "Please use conventional commits format:"
    echo "  feat: add new feature"
    echo "  fix: fix a bug"
    echo "  docs: update documentation"
    echo "  style: format code"
    echo "  refactor: refactor code"
    echo "  test: add tests"
    echo "  chore: maintenance tasks"
    echo ""
    echo "Example: feat(auth): add OAuth2 integration"
    exit 1
fi
EOF
    chmod +x .git/hooks/commit-msg
    
    print_success "Git hooks configured"
}

# Run environment validation
validate_environment() {
    print_step "Validating environment configuration"
    
    if python manage.py validate_environment --quiet; then
        print_success "Environment validation passed"
    else
        print_warning "Environment validation found issues - check configuration"
    fi
}

# Main setup function
main() {
    echo "=========================================="
    print_status "$BLUE" "🚀 Django Backend Boilerplate - Development Setup"
    echo "=========================================="
    echo
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Run setup steps
    check_python
    
    # Check for Docker (optional)
    docker_available=false
    if check_docker; then
        docker_available=true
    fi
    
    setup_virtual_env
    install_dependencies
    setup_mypy
    setup_pre_commit
    create_dev_env
    setup_git_hooks
    
    # Validate environment
    validate_environment
    
    echo
    print_success "Development environment setup completed!"
    echo
    print_info "Next steps:"
    echo "  1. Activate virtual environment: source $VENV_NAME/bin/activate"
    echo "  2. Update .env file with your configuration"
    echo "  3. Run migrations: python manage.py migrate"
    echo "  4. Create superuser: python manage.py createsuperuser"
    echo "  5. Start development server: python manage.py runserver"
    echo
    
    if [ "$docker_available" = true ]; then
        print_info "Docker is available. You can also use:"
        echo "  ./docker-cleanup.sh dev  # Start with Docker"
        echo
    fi
    
    print_info "Development tools available:"
    echo "  • Pre-commit hooks for code quality"
    echo "  • MyPy for type checking"
    echo "  • API documentation at /api/docs/"
    echo "  • Metrics at /api/v1/metrics/"
    echo "  • Health checks at /api/v1/health/"
    echo
    
    print_warning "Remember to:"
    echo "  • Update your .env file with real credentials"
    echo "  • Review pre-commit configuration in .pre-commit-config.yaml"
    echo "  • Run 'pre-commit run --all-files' after making changes"
}

# Run main function
main "$@"