from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db import connections
from django.conf import settings
import structlog

logger = structlog.get_logger(__name__)

class HealthCheckView(View):
    """
    Health check endpoint for Cloud Run health checks
    """

    def get(self, request):
        """
        Perform health checks and return status
        """
        health_status = {
            'status': 'healthy',
            'timestamp': request.META.get('HTTP_X_REQUEST_ID', 'unknown'),
            'environment': getattr(settings, 'DJANGO_ENV', 'unknown'),
            'checks': {}
        }

        # Check database connectivity
        try:
            db_conn = connections['default']
            db_conn.cursor()
            health_status['checks']['database'] = 'healthy'
            logger.info("Health check: database connection successful")
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['database'] = f'error: {str(e)}'
            logger.error("Health check: database connection failed", error=str(e))

        # Check basic Django functionality
        try:
            # Test that Django is responding
            health_status['checks']['django'] = 'healthy'
            logger.debug("Health check: Django responding")
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['django'] = f'error: {str(e)}'
            logger.error("Health check: Django check failed", error=str(e))

        # Return appropriate HTTP status code
        status_code = 200 if health_status['status'] == 'healthy' else 503

        return JsonResponse(health_status, status=status_code)
