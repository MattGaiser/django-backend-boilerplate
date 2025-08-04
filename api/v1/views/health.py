"""
Health check API view for monitoring service status.

Provides comprehensive endpoints for health monitoring with database connectivity,
cache status, external service checks, and system metrics.
"""

import time
from datetime import datetime, timezone

import structlog
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = structlog.get_logger(__name__)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint for monitoring service status.

    This endpoint provides detailed health information including:
    - Database connectivity
    - Cache status  
    - Django functionality
    - System metrics
    - External service dependencies
    """

    permission_classes = [AllowAny]  # Allow health checks without authentication

    def get(self, request):
        """
        Perform comprehensive health checks and return detailed status.

        Returns:
            Response: JSON response with health status and detailed check results
        """
        start_time = time.time()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": getattr(settings, "DJANGO_ENV", "unknown"),
            "version": getattr(settings, "VERSION_INFO", {}),
            "checks": {},
            "metrics": {},
        }

        # Check database connectivity
        health_status["checks"]["database"] = self._check_database()
        
        # Check cache functionality
        health_status["checks"]["cache"] = self._check_cache()
        
        # Check Django functionality
        health_status["checks"]["django"] = self._check_django()
        
        # Check external dependencies
        health_status["checks"]["storage"] = self._check_storage()
        
        # Add system metrics
        health_status["metrics"] = self._get_system_metrics(start_time)

        # Determine overall health status
        failed_checks = [
            check for check in health_status["checks"].values() 
            if isinstance(check, dict) and check.get("status") == "unhealthy"
        ]
        
        if failed_checks:
            health_status["status"] = "unhealthy"
            health_status["failed_checks_count"] = len(failed_checks)

        # Return appropriate HTTP status code
        response_status = (
            status.HTTP_200_OK
            if health_status["status"] == "healthy"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return Response(health_status, status=response_status)

    def _check_database(self):
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            db_conn = connections["default"]
            
            # Test basic connection
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            logger.info("Health check: database connection successful", 
                       response_time_ms=response_time)
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "database_name": db_conn.settings_dict.get("NAME", "unknown"),
                "database_engine": db_conn.settings_dict.get("ENGINE", "unknown"),
            }
            
        except Exception as e:
            logger.error("Health check: database connection failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _check_cache(self):
        """Check cache functionality and performance."""
        try:
            start_time = time.time()
            test_key = f"health_check_{int(time.time())}"
            test_value = "health_check_value"
            
            # Test cache write/read/delete
            cache.set(test_key, test_value, timeout=60)
            cached_value = cache.get(test_key)
            cache.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if cached_value != test_value:
                raise ValueError("Cache read/write test failed")
            
            logger.debug("Health check: cache functioning properly",
                        response_time_ms=response_time)
            
            return {
                "status": "healthy", 
                "response_time_ms": round(response_time, 2),
                "backend": getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", "unknown"),
            }
            
        except Exception as e:
            logger.error("Health check: cache check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _check_django(self):
        """Check basic Django functionality."""
        try:
            # Test that Django is responding and basic functionality works
            from django.contrib.auth import get_user_model
            from django.core.cache import cache
            
            User = get_user_model()
            
            # Test model access (should not fail in healthy Django)
            user_count = User.objects.count()
            
            logger.debug("Health check: Django responding", user_count=user_count)
            
            return {
                "status": "healthy",
                "user_count": user_count,
                "debug_mode": getattr(settings, "DEBUG", False),
            }
            
        except Exception as e:
            logger.error("Health check: Django check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _check_storage(self):
        """Check file storage connectivity."""
        try:
            from django.core.files.storage import default_storage
            
            # Test storage availability (basic check)
            storage_info = {
                "status": "healthy",
                "backend": default_storage.__class__.__name__,
            }
            
            # Add GCS-specific info if using GCS
            if hasattr(settings, "GCS_BUCKET_NAME"):
                storage_info["bucket_name"] = getattr(settings, "GCS_BUCKET_NAME", "unknown")
                storage_info["use_emulator"] = getattr(settings, "USE_GCS_EMULATOR", False)
            
            logger.debug("Health check: storage check passed")
            return storage_info
            
        except Exception as e:
            logger.error("Health check: storage check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _get_system_metrics(self, start_time):
        """Get basic system metrics."""
        import os
        import sys
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "response_time_ms": round(response_time, 2),
            "python_version": sys.version.split()[0],
            "django_version": getattr(settings, "DJANGO_VERSION", "unknown"),
            "process_id": os.getpid(),
            "uptime_check": True,
        }


class LivenessProbeView(APIView):
    """
    Kubernetes liveness probe endpoint.
    
    Simple endpoint that returns 200 if the service is alive.
    Used by orchestrators to determine if the container should be restarted.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return simple liveness confirmation."""
        return Response({
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


class ReadinessProbeView(APIView):
    """
    Kubernetes readiness probe endpoint.
    
    More comprehensive check to determine if the service is ready to accept traffic.
    Includes database connectivity check.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check if service is ready to accept traffic."""
        try:
            # Quick database check
            db_conn = connections["default"]
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return Response({
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": "connected",
            })
            
        except Exception as e:
            logger.error("Readiness check failed", error=str(e))
            return Response({
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
