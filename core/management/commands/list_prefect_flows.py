"""
Django management command to list available Prefect flows.
"""

import requests
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "List available Prefect flows"

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

        self.stdout.write(f"Fetching flows from Prefect server: {prefect_api_url}")

        try:
            # Get flows from Prefect API
            flows_url = f"{prefect_api_url.rstrip('/')}/flows"
            response = requests.get(flows_url, timeout=options["timeout"])

            if response.status_code == 200:
                try:
                    flows_data = response.json()
                    flows = (
                        flows_data
                        if isinstance(flows_data, list)
                        else flows_data.get("flows", [])
                    )

                    if flows:
                        self.stdout.write(
                            self.style.SUCCESS(f"Found {len(flows)} flow(s):")
                        )
                        self.stdout.write("")

                        for i, flow in enumerate(flows, 1):
                            flow_name = flow.get("name", "Unknown")
                            flow_id = flow.get("id", "Unknown")
                            flow_created = flow.get("created", "Unknown")

                            self.stdout.write(f"{i}. {flow_name}")
                            self.stdout.write(f"   ID: {flow_id}")
                            self.stdout.write(f"   Created: {flow_created}")
                            self.stdout.write("")

                        logger.info(
                            "Successfully retrieved Prefect flows", count=len(flows)
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING("No flows found on Prefect server")
                        )
                        logger.info("No flows found on Prefect server")

                except ValueError as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Could not parse response from Prefect server: {str(e)}"
                        )
                    )
                    logger.error("Failed to parse flows response", error=str(e))

            elif response.status_code == 404:
                self.stdout.write(
                    self.style.WARNING(
                        "Flows endpoint not found - server may not be fully configured"
                    )
                )
                logger.warning("Flows endpoint returned 404")

            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Prefect server returned status {response.status_code}"
                    )
                )
                logger.error(
                    "Flows request failed",
                    status_code=response.status_code,
                    response_text=response.text[:200],
                )

        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR("Could not connect to Prefect server"))
            logger.error("Failed to connect to Prefect server for flows", url=flows_url)

        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR("Request to Prefect server timed out"))
            logger.error("Flows request timed out", timeout=options["timeout"])

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching flows: {str(e)}"))
            logger.error("Unexpected error fetching flows", error=str(e))

        # Show example usage
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Example usage:")
        self.stdout.write("  python manage.py run_prefect_flow <flow_name>")
        self.stdout.write(
            "  python manage.py run_prefect_flow django-integration-example"
        )
