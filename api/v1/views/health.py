"""
Health check API view for monitoring service status.

Provides endpoints for health monitoring with database connectivity checks.
"""

import structlog
from django.conf import settings
from django.db import connections
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = structlog.get_logger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint for Cloud Run health checks and monitoring.

    This endpoint is used by load balancers and monitoring systems
    to verify service health and database connectivity.
    """

    permission_classes = [AllowAny]  # Allow health checks without authentication

    def get(self, request):
        """
        Perform health checks and return status.

        Returns:
            Response: JSON response with health status and check results
        """
        health_status = {
            "status": "healthy",
            "timestamp": request.META.get("HTTP_X_REQUEST_ID", "unknown"),
            "environment": getattr(settings, "DJANGO_ENV", "unknown"),
            "checks": {},
        }

        # Check database connectivity
        try:
            db_conn = connections["default"]
            db_conn.cursor()
            health_status["checks"]["database"] = "healthy"
            logger.info("Health check: database connection successful")
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = f"error: {str(e)}"
            logger.error("Health check: database connection failed", error=str(e))

        # Check basic Django functionality
        try:
            # Test that Django is responding
            health_status["checks"]["django"] = "healthy"
            logger.debug("Health check: Django responding")
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["django"] = f"error: {str(e)}"
            logger.error("Health check: Django check failed", error=str(e))

        # Return appropriate HTTP status code
        status_code = (
            status.HTTP_200_OK
            if health_status["status"] == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return Response(health_status, status=status_code)
