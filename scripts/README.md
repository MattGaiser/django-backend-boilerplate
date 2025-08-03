# Prefect Flow API Testing Script

This script tests the integration between Django and Prefect by logging into an appropriate admin account and calling the test Prefect flow via the REST API.

## Usage

### Quick Start

From the Django project root directory:

```bash
# Run with demo data (easiest option)
python manage.py seed_demo_data
python scripts/test_flow_api.py --verbose

# Or use the shell script wrapper
./scripts/test_flow_api.sh --verbose
```

### Command Line Options

```bash
python scripts/test_flow_api.py [OPTIONS]

Options:
  --base-url URL         Base URL for API calls (default: http://localhost:8000)
  --create-user          Create a new test user instead of using existing demo data
  --direct-flow-only     Only test direct flow execution (skip API testing)
  --verbose, -v          Enable verbose output
  --help                 Show help message
```

### Examples

```bash
# Test with default settings
python scripts/test_flow_api.py

# Test with verbose output and custom URL
python scripts/test_flow_api.py --verbose --base-url http://localhost:8001

# Test only direct flow execution (no API required)
python scripts/test_flow_api.py --direct-flow-only

# Create a new test user instead of using demo data
python scripts/test_flow_api.py --create-user --verbose
```

## What the Script Does

1. **Sets up Django environment** - Configures Django settings and imports required modules
2. **Creates or finds admin user** - Uses existing demo admin (admin@demo.com) or creates a test user
3. **Authenticates via API** - Obtains an authentication token using the login endpoint
4. **Triggers Prefect flow** - Calls the `/api/v1/flows/test-run/` endpoint to execute the hello world flow
5. **Displays results** - Shows the flow execution results and API response

## Authentication Requirements

The script requires a user with **ADMIN** or **SUPER_ADMIN** role in an organization to trigger flows. The demo data creates:

- **Email**: admin@demo.com
- **Password**: admin123  
- **Role**: Super Admin in "Demo Organization"

## API Endpoints Tested

- `POST /api/v1/auth/token/` - User authentication
- `GET /api/v1/auth/status/` - Authentication status check
- `POST /api/v1/flows/test-run/` - Trigger hello world Prefect flow

## Flow Tested

The script tests the `hello_world` flow located in `flows/hello_world_flow.py`, which:

- Executes two simple tasks (greeting and timestamp)
- Returns a structured result with message, timestamp, and status
- Demonstrates basic Prefect functionality

## Fallback Behavior

If the API test fails (e.g., due to database locks or server issues), the script automatically falls back to direct flow execution to verify that the Prefect integration itself is working.

## Expected Output

### Successful API Test
```
🚀 Starting Prefect Flow API Test
==================================================
✅ Found existing demo admin user: admin@demo.com
✅ Successfully obtained authentication token
✅ Authenticated as: Demo Admin (admin@demo.com)
✅ Flow triggered successfully!

==================================================
📊 TEST RESULTS
==================================================
✅ FLOW TRIGGER: SUCCESS
   Status: completed
   Flow Run ID: 3fd660f2-034e-4722-a4d8-d409d658be5a
   Message: Hello World flow triggered successfully.

🎯 FLOW EXECUTION RESULTS:
   Message: Hello from Prefect!
   Timestamp: 2025-08-03T02:53:21.775425
   Status: completed

✅ All tests passed! Prefect flow API integration is working correctly.
```

### Direct Flow Test
```
🚀 Starting Prefect Flow API Test
==================================================
🔬 Running in direct flow execution mode
✅ Flow executed successfully!

🎯 DIRECT FLOW EXECUTION RESULTS:
   Message: Hello from Prefect!
   Timestamp: 2025-08-03T02:53:43.467186
   Status: completed
```

## Prerequisites

- Django project with migrations applied (`python manage.py migrate`)
- Required dependencies installed (`pip install -r requirements.txt`)
- Optional: Demo data seeded (`python manage.py seed_demo_data`)
- Optional: Django development server running for full API test

## Troubleshooting

### Database Locked Error
If you see "database is locked" errors, the script will automatically fall back to direct flow execution. This happens when both the script and Django server access SQLite simultaneously.

### Permission Denied
Ensure the user has ADMIN or SUPER_ADMIN role in an organization. The demo data provides this setup automatically.

### Import Errors
Run from the Django project root directory and ensure all dependencies are installed.

### Network Connection Errors
If testing against a running server, ensure the Django development server is accessible at the specified URL.