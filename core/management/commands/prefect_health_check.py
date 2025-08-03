"""
Django management command to check Prefect server health and connectivity.
"""

import requests
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Check Prefect server health and connectivity"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=10,
            help="Request timeout in seconds (default: 10)",
        )

    def handle(self, *args, **options):
        prefect_api_url = getattr(settings, "PREFECT_API_URL", None)

        if not prefect_api_url:
            self.stdout.write(
                self.style.ERROR("PREFECT_API_URL not configured in settings")
            )
            return

        self.stdout.write(f"Checking Prefect server at: {prefect_api_url}")

        try:
            # Test basic connectivity
            health_url = f"{prefect_api_url.rstrip('/')}/health"
            response = requests.get(health_url, timeout=options["timeout"])

            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS("✅ Prefect server health check passed")
                )
                logger.info(
                    "Prefect server health check successful",
                    url=health_url,
                    status_code=response.status_code,
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Prefect server responded with status {response.status_code}"
                    )
                )
                logger.warning(
                    "Prefect server health check returned non-200 status",
                    url=health_url,
                    status_code=response.status_code,
                )

        except requests.exceptions.ConnectionError:
            self.stdout.write(
                self.style.ERROR("❌ Could not connect to Prefect server")
            )
            logger.error("Failed to connect to Prefect server", url=prefect_api_url)

        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR("❌ Prefect server request timed out"))
            logger.error(
                "Prefect server request timed out",
                url=prefect_api_url,
                timeout=options["timeout"],
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error checking Prefect server: {str(e)}")
            )
            logger.error(
                "Unexpected error checking Prefect server",
                error=str(e),
                url=prefect_api_url,
            )

        # Test API endpoint
        try:
            api_url = f"{prefect_api_url.rstrip('/')}"
            response = requests.get(api_url, timeout=options["timeout"])

            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS("✅ Prefect API endpoint accessible")
                )

                # Try to get server info if available
                try:
                    data = response.json()
                    if "message" in data:
                        self.stdout.write(f'Server message: {data["message"]}')
                except ValueError:
                    pass  # Not JSON response

            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Prefect API endpoint returned status {response.status_code}"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Could not access Prefect API: {str(e)}")
            )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Prefect Configuration:")
        self.stdout.write(f"  PREFECT_API_URL: {prefect_api_url}")
        self.stdout.write(
            f'  PREFECT_SERVER_HOST: {getattr(settings, "PREFECT_SERVER_HOST", "Not set")}'
        )
        self.stdout.write(
            f'  PREFECT_SERVER_PORT: {getattr(settings, "PREFECT_SERVER_PORT", "Not set")}'
        )
