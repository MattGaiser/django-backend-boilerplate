"""
API views for triggering Prefect flows.

This module provides REST API endpoints for triggering and monitoring
Prefect flows with proper authentication, authorization, and logging.
"""

import structlog
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.v1.serializers.flow_trigger import FlowTriggerResponseSerializer
from common.permissions.org_scoped import IsOrgAdmin

# Get structured logger
logger = structlog.get_logger(__name__)


class TriggerHelloWorldFlowView(APIView):
    """
    API view for triggering the hello world Prefect flow.

    This endpoint allows organization administrators to trigger a simple
    hello world flow for testing purposes. The flow execution is logged
    with structured logging including user and organization context.

    **Required Permissions:**
    - User must be authenticated
    - User must have ADMIN role in their default organization

    **Request:**
    - Method: POST
    - Body: {} (empty JSON object)

    **Response:**
    - 200: Flow triggered successfully
    - 401: User not authenticated
    - 403: User does not have admin permissions
    - 500: Flow failed to trigger

    **Example Response:**
    ```json
    {
        "status": "submitted",
        "flow_run_id": "9f04eb04-eee0-41e6-881e-3a1213f3a7e4",
        "message": "Hello World flow triggered successfully.",
        "flow_result": {
            "message": "Hello from Prefect!",
            "timestamp": "2025-08-02T20:44:04.677833",
            "status": "completed"
        }
    }
    ```
    """

    permission_classes = [IsOrgAdmin]

    def get_organization(self):
        """
        Get the organization context for this request.

        Returns the user's default organization for permission checking.
        """
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            return self.request.user.get_default_organization()
        return None

    def post(self, request, *args, **kwargs):
        """
        Trigger the hello world Prefect flow.
        """
        user = request.user
        organization = user.get_default_organization()

        # Log the flow trigger attempt with structured logging
        logger.info(
            "flow_trigger_attempted",
            user_id=str(user.id),
            user_email=user.email,
            organization_id=str(organization.id) if organization else None,
            organization_name=organization.name if organization else None,
            flow_name="hello_world",
            endpoint="trigger_hello_world_flow",
        )

        try:
            # Import and trigger the Prefect flow
            from flows.hello_world_flow import hello_world

            # Execute the flow directly and get the result
            # For simple flows, we can run them synchronously
            flow_result = hello_world()

            # For async execution, generate a mock flow run ID
            import uuid

            flow_run_id = str(uuid.uuid4())

            # Prepare response data
            response_data = {
                "status": "completed",
                "flow_run_id": flow_run_id,
                "message": str(_("Hello World flow triggered successfully.")),
                "flow_result": flow_result,
            }

            # Log successful flow trigger
            logger.info(
                "flow_trigger_success",
                user_id=str(user.id),
                user_email=user.email,
                organization_id=str(organization.id) if organization else None,
                organization_name=organization.name if organization else None,
                flow_name="hello_world",
                flow_run_id=flow_run_id,
                endpoint="trigger_hello_world_flow",
            )

            # Serialize and return response
            serializer = FlowTriggerResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except ImportError as e:
            error_msg = f"Failed to import hello_world flow: {str(e)}"
            logger.error(
                "flow_import_error",
                user_id=str(user.id),
                organization_id=str(organization.id) if organization else None,
                flow_name="hello_world",
                error=error_msg,
                endpoint="trigger_hello_world_flow",
            )

            response_data = {
                "status": "failed",
                "flow_run_id": None,
                "message": str(_("Flow import failed. Please contact support.")),
                "flow_result": None,
            }

            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            error_msg = f"Failed to trigger hello_world flow: {str(e)}"
            logger.error(
                "flow_trigger_error",
                user_id=str(user.id),
                organization_id=str(organization.id) if organization else None,
                flow_name="hello_world",
                error=error_msg,
                endpoint="trigger_hello_world_flow",
            )

            response_data = {
                "status": "failed",
                "flow_run_id": None,
                "message": str(
                    _("Flow trigger failed. Please try again or contact support.")
                ),
                "flow_result": None,
            }

            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create the view instance for URL routing
trigger_hello_world_flow = TriggerHelloWorldFlowView.as_view()
