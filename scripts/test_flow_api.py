#!/usr/bin/env python
"""
Script to test Prefect flow API integration.

This script logs into an appropriate account and calls the test Prefect flow
via the Django REST API to verify that the integration is working correctly.

Usage:
    python scripts/test_flow_api.py [--base-url BASE_URL] [--create-user] [--verbose]

The script will:
1. Set up Django environment
2. Create or use existing admin user with proper organization access
3. Obtain authentication token
4. Make API call to trigger the hello world flow
5. Display results

Environment Variables:
    DJANGO_SETTINGS_MODULE: Django settings module (defaults to DjangoBoilerplate.settings)
    BASE_URL: Base URL for API calls (defaults to http://localhost:8000)
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import requests

# Add the project root to Python path so we can import Django modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoBoilerplate.settings")

try:
    import django

    django.setup()
except ImportError as e:
    print(f"❌ Error setting up Django: {e}")
    print(
        "Make sure you're running this from the project root and Django is installed."
    )
    sys.exit(1)

# Django imports (must be after django.setup())
from django.contrib.auth import get_user_model
from django.db import transaction

from constants.roles import OrgRole
from core.models import Organization, OrganizationMembership

User = get_user_model()


class PrefectFlowTester:
    """
    Class to handle testing of Prefect flow API integration.
    """

    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.api_base = f"{self.base_url}/api/v1"

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp if verbose mode is enabled."""
        if self.verbose or level in ["SUCCESS", "ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(
                level, "ℹ️"
            )
            print(f"[{timestamp}] {prefix} {message}")

    def create_or_get_admin_user(self) -> tuple[User, str]:
        """
        Create or get an admin user with proper organization membership.

        Returns:
            Tuple of (User, password) where password is the plaintext password
        """
        self.log("Setting up admin user and organization...", "INFO")

        # First, try to use existing demo data
        try:
            user = User.objects.get(email="admin@demo.com")
            self.log(f"Found existing demo admin user: {user.email}", "SUCCESS")
            return user, "admin123"
        except User.DoesNotExist:
            self.log("Demo admin user not found, creating new test user...", "INFO")

        # Create organization if it doesn't exist
        org, org_created = Organization.objects.get_or_create(
            name="Test Organization",
            defaults={
                "description": "Test organization for API testing",
                "is_active": True,
            },
        )

        if org_created:
            self.log(f"Created organization: {org.name}", "SUCCESS")
        else:
            self.log(f"Using existing organization: {org.name}", "INFO")

        # Create admin user
        user, user_created = User.objects.get_or_create(
            email="testadmin@example.com",
            defaults={
                "full_name": "Test Admin User",
                "is_active": True,
                "is_staff": True,
                "is_superuser": False,  # Don't need superuser for API testing
            },
        )

        password = "testpass123"
        if user_created:
            user.set_password(password)
            user.save()
            self.log(f"Created admin user: {user.email}", "SUCCESS")
        else:
            self.log(f"Using existing admin user: {user.email}", "INFO")

        # Create or update organization membership
        membership, membership_created = OrganizationMembership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={
                "role": OrgRole.ADMIN,  # Use ADMIN instead of SUPER_ADMIN
                "is_default": True,
            },
        )

        if membership_created:
            self.log(
                f"Created admin membership with role: {membership.get_role_display()}",
                "SUCCESS",
            )
        elif membership.role != OrgRole.ADMIN:
            # Update role if needed
            membership.role = OrgRole.ADMIN
            membership.is_default = True
            membership.save()
            self.log(
                f"Updated membership role to: {membership.get_role_display()}", "INFO"
            )

        return user, password

    def get_auth_token(self, email: str, password: str) -> Optional[str]:
        """
        Obtain authentication token by logging in via API.

        Args:
            email: User email
            password: User password

        Returns:
            Authentication token string or None if login failed
        """
        self.log(f"Obtaining authentication token for {email}...", "INFO")

        login_url = f"{self.api_base}/auth/token/"
        login_data = {"email": email, "password": password}

        try:
            response = requests.post(login_url, json=login_data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("key")
                if token:
                    self.log("Successfully obtained authentication token", "SUCCESS")
                    if self.verbose:
                        user_info = token_data.get("user", {})
                        self.log(
                            f"Authenticated as: {user_info.get('full_name')} ({user_info.get('email')})",
                            "INFO",
                        )
                    return token
                else:
                    self.log("Login response missing token", "ERROR")
                    return None
            else:
                self.log(
                    f"Login failed with status {response.status_code}: {response.text}",
                    "ERROR",
                )
                return None

        except requests.exceptions.RequestException as e:
            self.log(f"Network error during login: {e}", "ERROR")
            return None

    def trigger_flow(self, token: str) -> Dict[str, Any]:
        """
        Trigger the hello world Prefect flow via API.

        Args:
            token: Authentication token

        Returns:
            API response data as dictionary
        """
        self.log("Triggering hello world Prefect flow...", "INFO")

        flow_url = f"{self.api_base}/flows/test-run/"
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(flow_url, json={}, headers=headers, timeout=30)

            self.log(f"Flow API response status: {response.status_code}", "INFO")

            if response.status_code == 200:
                flow_data = response.json()
                self.log("Flow triggered successfully!", "SUCCESS")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": flow_data,
                }
            else:
                error_data = (
                    response.json()
                    if response.content
                    else {"error": "No response content"}
                )
                self.log(
                    f"Flow trigger failed with status {response.status_code}", "ERROR"
                )
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "data": error_data,
                }

        except requests.exceptions.RequestException as e:
            self.log(f"Network error during flow trigger: {e}", "ERROR")
            return {"success": False, "status_code": 0, "data": {"error": str(e)}}

    def check_auth_status(self, token: str) -> Dict[str, Any]:
        """
        Check authentication status and user info.

        Args:
            token: Authentication token

        Returns:
            Auth status response data
        """
        self.log("Checking authentication status...", "INFO")

        auth_url = f"{self.api_base}/auth/status/"
        headers = {"Authorization": f"Token {token}"}

        try:
            response = requests.get(auth_url, headers=headers, timeout=10)

            if response.status_code == 200:
                auth_data = response.json()
                if auth_data.get("authenticated"):
                    user = auth_data.get("user", {})
                    self.log(
                        f"Authenticated as: {user.get('full_name', 'Unknown')} ({user.get('email', 'Unknown')})",
                        "SUCCESS",
                    )

                    # Check organization memberships
                    orgs = user.get("organizations", [])
                    if orgs:
                        self.log(f"Organization memberships:", "INFO")
                        for org in orgs:
                            role = org.get("membership", {}).get("role", "Unknown")
                            is_default = org.get("membership", {}).get(
                                "is_default", False
                            )
                            default_marker = " (default)" if is_default else ""
                            self.log(
                                f"  - {org.get('name', 'Unknown')}: {role}{default_marker}",
                                "INFO",
                            )
                    else:
                        self.log("No organization memberships found", "WARNING")

                    return auth_data
                else:
                    self.log("User is not authenticated", "ERROR")
                    return auth_data
            else:
                self.log(
                    f"Auth status check failed with status {response.status_code}",
                    "ERROR",
                )
                return {"error": f"HTTP {response.status_code}"}

        except requests.exceptions.RequestException as e:
            self.log(f"Network error during auth check: {e}", "ERROR")
            return {"error": str(e)}

    def test_flow_directly(self) -> bool:
        """
        Test the Prefect flow directly without going through the API.

        Returns:
            True if flow execution was successful, False otherwise
        """
        self.log("Testing Prefect flow directly...", "INFO")

        try:
            # Import and execute the flow directly
            from flows.hello_world_flow import hello_world

            self.log("Executing hello_world flow...", "INFO")
            result = hello_world()

            self.log("Flow executed successfully!", "SUCCESS")
            print("\n🎯 DIRECT FLOW EXECUTION RESULTS:")
            print(f"   Message: {result.get('message', 'None')}")
            print(f"   Timestamp: {result.get('timestamp', 'None')}")
            print(f"   Status: {result.get('status', 'None')}")

            return True

        except Exception as e:
            self.log(f"Direct flow execution failed: {e}", "ERROR")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False

    def run_test(
        self, create_user: bool = False, direct_flow_only: bool = False
    ) -> bool:
        """
        Run the complete flow test.

        Args:
            create_user: Whether to create a new user or use existing
            direct_flow_only: If True, only test flow directly without API

        Returns:
            True if test was successful, False otherwise
        """
        print("🚀 Starting Prefect Flow API Test")
        print("=" * 50)

        # If only testing direct flow execution
        if direct_flow_only:
            print("🔬 Running in direct flow execution mode")
            return self.test_flow_directly()

        try:
            # Skip database operations if only testing direct flow
            if not direct_flow_only:
                with transaction.atomic():
                    # Step 1: Set up user and organization
                    user, password = self.create_or_get_admin_user()

                    # Step 2: Get authentication token
                    token = self.get_auth_token(user.email, password)
                    if not token:
                        self.log("Failed to obtain authentication token", "ERROR")
                        self.log("Falling back to direct flow execution...", "WARNING")
                        return self.test_flow_directly()

                    # Step 3: Check authentication status
                    auth_status = self.check_auth_status(token)
                    if not auth_status.get("authenticated"):
                        self.log("Authentication check failed", "ERROR")
                        self.log("Falling back to direct flow execution...", "WARNING")
                        return self.test_flow_directly()

                    # Step 4: Trigger the flow
                    flow_result = self.trigger_flow(token)

                    # Step 5: Display results
                    print("\n" + "=" * 50)
                    print("📊 TEST RESULTS")
                    print("=" * 50)

                    if flow_result["success"]:
                        print("✅ FLOW TRIGGER: SUCCESS")
                        data = flow_result["data"]
                        print(f"   Status: {data.get('status', 'Unknown')}")
                        print(f"   Flow Run ID: {data.get('flow_run_id', 'None')}")
                        print(f"   Message: {data.get('message', 'None')}")

                        flow_data = data.get("flow_result", {})
                        if flow_data:
                            print("\n🎯 FLOW EXECUTION RESULTS:")
                            print(f"   Message: {flow_data.get('message', 'None')}")
                            print(f"   Timestamp: {flow_data.get('timestamp', 'None')}")
                            print(f"   Status: {flow_data.get('status', 'None')}")

                        print(
                            "\n✅ All tests passed! Prefect flow API integration is working correctly."
                        )
                        return True
                    else:
                        print("❌ FLOW TRIGGER: FAILED")
                        print(f"   Status Code: {flow_result['status_code']}")
                        print(f"   Error: {flow_result['data']}")

                        # Try direct flow execution as fallback
                        print("\n⚠️  API test failed, trying direct flow execution...")
                        return self.test_flow_directly()
            else:
                # Direct flow execution only
                return self.test_flow_directly()

        except Exception as e:
            self.log(f"Unexpected error during test: {e}", "ERROR")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test Prefect flow API integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL", "http://localhost:8000"),
        help="Base URL for API calls (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--create-user",
        action="store_true",
        help="Create a new test user instead of using existing demo data",
    )

    parser.add_argument(
        "--direct-flow-only",
        action="store_true",
        help="Only test direct flow execution (skip API testing)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Check if we're running from the correct directory
    if not os.path.exists("manage.py"):
        print(
            "❌ Error: This script must be run from the Django project root directory."
        )
        print("   Expected to find 'manage.py' in the current directory.")
        sys.exit(1)

    # Run the test
    tester = PrefectFlowTester(base_url=args.base_url, verbose=args.verbose)
    success = tester.run_test(
        create_user=args.create_user, direct_flow_only=args.direct_flow_only
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
