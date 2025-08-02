"""
API views for triggering Prefect flows.

This module provides REST API endpoints for triggering and monitoring
Prefect flows with proper authentication, authorization, and logging.
"""

import structlog
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from constants.roles import OrgRole
from api.v1.serializers.flow_trigger import FlowTriggerResponseSerializer


# Get structured logger
logger = structlog.get_logger(__name__)


def _check_admin_permission(request):
    """
    Check if the user has admin permission in their default organization.
    
    Args:
        request: HTTP request object
        
    Returns:
        tuple: (has_permission: bool, error_response: Response or None)
    """
    user = request.user
    
    if not user or not user.is_authenticated:
        return False, Response(
            {"detail": str(_("Authentication credentials were not provided."))},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get user's default organization
    organization = user.get_default_organization()
    if not organization:
        return False, Response(
            {"detail": str(_("User must belong to an organization to perform this action."))},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user has admin role in the organization
    user_role = user.get_role(organization)
    if user_role != OrgRole.ADMIN:
        return False, Response(
            {"detail": str(_("Admin permissions required to trigger flows."))},
            status=status.HTTP_403_FORBIDDEN
        )
    
    return True, None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_hello_world_flow(request):
    """
    Trigger the hello world Prefect flow.
    
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
    # Check admin permissions
    has_permission, error_response = _check_admin_permission(request)
    if not has_permission:
        return error_response
    
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
        endpoint="trigger_hello_world_flow"
    )
    
    try:
        # Import and trigger the Prefect flow
        from flows.hello_world_flow import hello_world
        
        # Submit the flow for execution
        flow_run = hello_world.submit()
        
        # Get the flow run ID
        flow_run_id = str(flow_run.id) if flow_run else None
        
        # Prepare response data
        response_data = {
            "status": "submitted",
            "flow_run_id": flow_run_id,
            "message": str(_("Hello World flow triggered successfully.")),
            "flow_result": None  # Will be populated when flow completes
        }
        
        # For demo purposes, we'll wait for the flow to complete and get the result
        # In production, you might want to return immediately and check status separately
        try:
            if flow_run:
                # Wait for completion (with timeout for safety)
                result = flow_run.result(timeout=30)
                response_data["flow_result"] = result
                response_data["status"] = "completed"
        except Exception as e:
            logger.warning(
                "flow_result_retrieval_failed",
                user_id=str(user.id),
                organization_id=str(organization.id) if organization else None,
                flow_run_id=flow_run_id,
                error=str(e)
            )
            # Don't fail the request if we can't get the result
            pass
        
        # Log successful flow trigger
        logger.info(
            "flow_trigger_success",
            user_id=str(user.id),
            user_email=user.email,
            organization_id=str(organization.id) if organization else None,
            organization_name=organization.name if organization else None,
            flow_name="hello_world",
            flow_run_id=flow_run_id,
            endpoint="trigger_hello_world_flow"
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
            endpoint="trigger_hello_world_flow"
        )
        
        response_data = {
            "status": "failed",
            "flow_run_id": None,
            "message": str(_("Flow import failed. Please contact support.")),
            "flow_result": None
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
            endpoint="trigger_hello_world_flow"
        )
        
        response_data = {
            "status": "failed",
            "flow_run_id": None,
            "message": str(_("Flow trigger failed. Please try again or contact support.")),
            "flow_result": None
        }
        
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)