"""
Management command to test structured logging functionality.

This command demonstrates how structured logging works in management commands
and provides a way to test the logging configuration.
"""

import uuid

from django.core.management.base import BaseCommand

from core.logging import get_structured_logger, set_request_context


class Command(BaseCommand):
    """Management command to test structured logging."""

    help = "Test structured logging functionality in management commands"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--user-id",
            type=str,
            help="User ID to use in logging context",
        )
        parser.add_argument(
            "--org-id",
            type=str,
            help="Organization ID to use in logging context",
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        # Set up logging context for management command
        request_id = str(uuid.uuid4())
        user_id = options.get("user_id")
        org_id = options.get("org_id")

        set_request_context(request_id, user_id, org_id)

        # Get structured logger
        logger = get_structured_logger(__name__)

        # Log various messages to test structured logging
        logger.info("Management command started", command="test_structured_logging")

        logger.debug("Debug message with context")

        logger.info("Processing data", items_count=100, operation="test_operation")

        logger.warning(
            "Warning message",
            warning_type="test_warning",
            details="This is a test warning",
        )

        try:
            # Simulate an operation that might fail
            if options.get("user_id") == "fail":
                raise ValueError("Simulated error for testing")

            logger.info("Operation completed successfully")

        except Exception as e:
            logger.error(
                "Operation failed",
                error_type=e.__class__.__name__,
                error_message=str(e),
                exc_info=True,
            )

        logger.info("Management command completed")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully tested structured logging with request_id: {request_id}"
            )
        )
