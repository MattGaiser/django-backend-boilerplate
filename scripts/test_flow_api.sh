#!/bin/bash
#
# Simple wrapper script to test Prefect flow API integration
#
# This script runs the Python test script with the Django environment properly configured.
# It assumes the Django development server is running on localhost:8000.
#
# Usage:
#   ./scripts/test_flow_api.sh [--verbose] [--create-user] [--base-url URL]
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

echo "🔧 Testing Prefect Flow API Integration"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Make sure you're running this from the Django project root."
    exit 1
fi

# Set Django settings if not already set
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-DjangoBoilerplate.settings}"

# Run the Python test script
python scripts/test_flow_api.py "$@"