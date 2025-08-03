# Testing Commands

This document provides a quick reference for running tests in the Django Backend Boilerplate project.

## Quick Start

Run all tests with a single command:

```bash
./run-tests-minimal.sh
```

## Available Test Runners

### 1. Minimal Test Runner (Recommended)
**File:** `run-tests-minimal.sh`  
**Description:** Fast test runner with just Django + PostgreSQL

```bash
# Run tests quickly
./run-tests-minimal.sh

# Run with verbose output
./run-tests-minimal.sh --verbose

# Get help
./run-tests-minimal.sh --help
```

**Pros:**
- ✅ Fastest startup time
- ✅ Minimal resource usage
- ✅ Essential services only
- ✅ Great for development

**Cons:**
- ❌ Skips integration tests requiring external services

### 2. Full Test Runner
**File:** `run-tests.sh`  
**Description:** Complete test suite with all services

```bash
# Run full test suite
./run-tests.sh

# Run with verbose output
./run-tests.sh --verbose

# Run with fast mode (skip some services)
./run-tests.sh --fast
```

**Pros:**
- ✅ Tests all integrations
- ✅ Includes Prefect, GCS emulator
- ✅ Production-like environment

**Cons:**
- ❌ Slower startup time
- ❌ Higher resource usage

### 3. Alternative Runners

#### Simple Test Runner
**File:** `run-tests-simple.sh`
- Alternative minimal approach
- Different implementation strategy

#### Direct Test Runner  
**File:** `run-tests-direct.sh`
- Single container approach
- Uses SQLite for speed

## Test Framework

The project uses **pytest** with the following features:
- Django integration via `pytest-django`
- Factory Boy for test data generation
- Coverage reporting with `pytest-cov`
- Parallel execution with `pytest-xdist`

## Test Structure

```
tests/
├── core/tests/          # Core Django model tests
│   ├── test_models.py
│   ├── test_signals.py
│   ├── test_rbac.py
│   └── ...
└── api/v1/tests/        # API endpoint tests
    ├── test_auth.py
    ├── test_users.py
    ├── test_permissions.py
    └── ...
```

## Environment Configuration

Tests use the `.env.test` file for configuration:
- Test database: `django_test_db`
- Debug mode: `false`
- Isolated test environment

## What Gets Tested

### ✅ Passing Tests (Core Infrastructure)
- **Permissions & RBAC** (18 tests) - All passing
- **User management** 
- **Organization models**
- **Authentication flows**

### 🔄 Tests with Dependencies
Some tests may require additional services:
- Storage tests need GCS emulator
- Flow tests need Prefect integration
- Integration tests need external APIs

## Docker Configuration

Tests run in isolated Docker containers:
- **Database:** PostgreSQL 16 with temporary storage
- **Application:** Django with development dependencies
- **Isolation:** Each test run uses fresh containers

## Performance

| Runner | Startup Time | Resource Usage | Test Coverage |
|--------|-------------|----------------|---------------|
| Minimal | ~5-10s | Low | Core + API |
| Full | ~30-60s | High | Complete |
| Direct | ~5-8s | Minimal | Core only |

## Troubleshooting

### Common Issues

1. **"pytest not found"**
   ```bash
   # Solution: Development dependencies are installed automatically
   ./run-tests-minimal.sh --verbose
   ```

2. **Database connection issues**
   ```bash
   # Solution: Wait for database to be ready (handled automatically)
   ```

3. **Permission denied**
   ```bash
   # Solution: Make scripts executable
   chmod +x run-tests-*.sh
   ```

4. **Docker not running**
   ```bash
   # Solution: Start Docker service
   sudo systemctl start docker  # Linux
   # or start Docker Desktop
   ```

### Getting Help

```bash
# Show help for any test runner
./run-tests-minimal.sh --help
./run-tests.sh --help
```

### Verbose Output

Add `--verbose` to any command to see detailed test output:
```bash
./run-tests-minimal.sh --verbose
```

## Integration with CI/CD

For automated testing, use the minimal runner:

```yaml
# Example GitHub Actions
- name: Run tests
  run: ./run-tests-minimal.sh
```

For comprehensive testing, use the full runner:

```yaml
# Example comprehensive testing
- name: Run full test suite  
  run: ./run-tests.sh
```

## Development Workflow

1. **Quick feedback:** Use `./run-tests-minimal.sh` during development
2. **Pre-commit:** Run `./run-tests.sh` before committing
3. **CI/CD:** Use minimal runner for speed, full runner for releases

---

Need help? Check the individual script help:
```bash
./run-tests-minimal.sh --help
```