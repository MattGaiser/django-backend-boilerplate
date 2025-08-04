"""
Metrics API views for monitoring and observability.

Provides endpoints for application metrics, system status, and performance monitoring
compatible with Prometheus and other monitoring systems.
"""

import time
from datetime import datetime, timedelta, timezone

import structlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connections
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Organization, OrganizationMembership

logger = structlog.get_logger(__name__)
User = get_user_model()


class MetricsView(APIView):
    """
    Application metrics endpoint for monitoring systems.
    
    Returns custom application metrics in a format suitable for
    Prometheus scraping or other monitoring tools.
    """
    
    permission_classes = [AllowAny]  # Metrics should be accessible to monitoring systems
    
    def get(self, request):
        """
        Return application metrics in JSON format.
        
        Returns:
            Response: JSON response with application metrics
        """
        try:
            metrics = self._collect_application_metrics()
            
            return Response({
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "collection_time_ms": metrics.get("collection_time_ms", 0),
            })
            
        except Exception as e:
            logger.error("Failed to collect application metrics", error=str(e))
            return Response({
                "error": "Failed to collect metrics",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _collect_application_metrics(self):
        """Collect custom application metrics."""
        start_time = time.time()
        
        metrics = {}
        
        # Database metrics
        try:
            metrics.update(self._get_database_metrics())
        except Exception as e:
            logger.warning("Failed to collect database metrics", error=str(e))
            metrics["database_error"] = str(e)
        
        # User and organization metrics
        try:
            metrics.update(self._get_user_metrics())
        except Exception as e:
            logger.warning("Failed to collect user metrics", error=str(e))
            metrics["user_metrics_error"] = str(e)
        
        # Cache metrics
        try:
            metrics.update(self._get_cache_metrics())
        except Exception as e:
            logger.warning("Failed to collect cache metrics", error=str(e))
            metrics["cache_metrics_error"] = str(e)
        
        # System metrics
        metrics.update(self._get_system_metrics())
        
        # Collection performance
        collection_time = (time.time() - start_time) * 1000
        metrics["collection_time_ms"] = round(collection_time, 2)
        
        return metrics
    
    def _get_database_metrics(self):
        """Get database-related metrics."""
        metrics = {}
        
        # Query counts
        metrics["total_users"] = User.objects.count()
        metrics["active_users"] = User.objects.filter(is_active=True).count()
        metrics["total_organizations"] = Organization.objects.count()
        metrics["total_memberships"] = OrganizationMembership.objects.count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        metrics["users_created_24h"] = User.objects.filter(created_at__gte=yesterday).count()
        metrics["organizations_created_24h"] = Organization.objects.filter(created_at__gte=yesterday).count()
        
        # Database connection info
        db_conn = connections["default"]
        metrics["database_name"] = db_conn.settings_dict.get("NAME", "unknown")
        metrics["database_engine"] = db_conn.settings_dict.get("ENGINE", "unknown").split(".")[-1]
        
        return metrics
    
    def _get_user_metrics(self):
        """Get user-related metrics."""
        from constants.roles import OrgRole
        
        metrics = {}
        
        # User role distribution
        admin_count = OrganizationMembership.objects.filter(role=OrgRole.ADMIN).count()
        manager_count = OrganizationMembership.objects.filter(role=OrgRole.MANAGER).count()
        viewer_count = OrganizationMembership.objects.filter(role=OrgRole.VIEWER).count()
        
        metrics["admin_users"] = admin_count
        metrics["manager_users"] = manager_count
        metrics["viewer_users"] = viewer_count
        
        # Login activity (approximation based on last_login)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        metrics["users_logged_in_7d"] = User.objects.filter(
            last_login__gte=week_ago
        ).count()
        
        # Superuser count
        metrics["superusers"] = User.objects.filter(is_superuser=True).count()
        
        return metrics
    
    def _get_cache_metrics(self):
        """Get cache-related metrics."""
        metrics = {}
        
        try:
            # Test cache performance
            start_time = time.time()
            test_key = f"metrics_test_{int(time.time())}"
            cache.set(test_key, "test_value", timeout=10)
            cache.get(test_key)
            cache.delete(test_key)
            cache_response_time = (time.time() - start_time) * 1000
            
            metrics["cache_response_time_ms"] = round(cache_response_time, 2)
            metrics["cache_backend"] = getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", "unknown")
            metrics["cache_status"] = "healthy"
            
        except Exception as e:
            metrics["cache_status"] = "unhealthy"
            metrics["cache_error"] = str(e)
        
        return metrics
    
    def _get_system_metrics(self):
        """Get system-related metrics."""
        import os
        import sys
        
        metrics = {
            "python_version": sys.version.split()[0],
            "django_debug": getattr(settings, "DEBUG", False),
            "environment": getattr(settings, "DJANGO_ENV", "unknown"),
            "process_id": os.getpid(),
        }
        
        # Version information if available
        version_info = getattr(settings, "VERSION_INFO", {})
        if version_info:
            metrics.update({
                f"version_{k}": v for k, v in version_info.items()
            })
        
        return metrics


class PrometheusMetricsView(APIView):
    """
    Prometheus-compatible metrics endpoint.
    
    Returns metrics in Prometheus exposition format for scraping by Prometheus server.
    Note: Django-prometheus automatically provides many Django metrics.
    This endpoint adds custom application metrics.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Return custom metrics in Prometheus format.
        
        Returns:
            HttpResponse: Plain text response with Prometheus metrics
        """
        try:
            metrics_data = self._generate_prometheus_metrics()
            
            return HttpResponse(
                metrics_data,
                content_type="text/plain; version=0.0.4; charset=utf-8"
            )
            
        except Exception as e:
            logger.error("Failed to generate Prometheus metrics", error=str(e))
            return HttpResponse(
                f"# ERROR: Failed to generate metrics: {str(e)}\n",
                content_type="text/plain",
                status=500
            )
    
    def _generate_prometheus_metrics(self):
        """Generate Prometheus-format metrics."""
        lines = []
        
        # Add custom application metrics
        try:
            # User metrics
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            lines.extend([
                "# HELP django_users_total Total number of users",
                "# TYPE django_users_total gauge",
                f"django_users_total {total_users}",
                "",
                "# HELP django_users_active Number of active users", 
                "# TYPE django_users_active gauge",
                f"django_users_active {active_users}",
                "",
            ])
            
            # Organization metrics
            total_orgs = Organization.objects.count()
            lines.extend([
                "# HELP django_organizations_total Total number of organizations",
                "# TYPE django_organizations_total gauge", 
                f"django_organizations_total {total_orgs}",
                "",
            ])
            
            # Role distribution
            from constants.roles import OrgRole
            admin_count = OrganizationMembership.objects.filter(role=OrgRole.ADMIN).count()
            manager_count = OrganizationMembership.objects.filter(role=OrgRole.MANAGER).count()
            viewer_count = OrganizationMembership.objects.filter(role=OrgRole.VIEWER).count()
            
            lines.extend([
                "# HELP django_users_by_role Number of users by role",
                "# TYPE django_users_by_role gauge",
                f'django_users_by_role{{role="admin"}} {admin_count}',
                f'django_users_by_role{{role="manager"}} {manager_count}',
                f'django_users_by_role{{role="viewer"}} {viewer_count}',
                "",
            ])
            
            # Cache health
            try:
                start_time = time.time()
                cache.set("prometheus_test", "test", timeout=10)
                cache.get("prometheus_test")
                cache.delete("prometheus_test")
                cache_latency = (time.time() - start_time) * 1000
                
                lines.extend([
                    "# HELP django_cache_latency_ms Cache operation latency in milliseconds",
                    "# TYPE django_cache_latency_ms gauge",
                    f"django_cache_latency_ms {cache_latency:.2f}",
                    "",
                    "# HELP django_cache_healthy Cache health status (1=healthy, 0=unhealthy)",
                    "# TYPE django_cache_healthy gauge",
                    "django_cache_healthy 1",
                    "",
                ])
            except Exception:
                lines.extend([
                    "# HELP django_cache_healthy Cache health status (1=healthy, 0=unhealthy)", 
                    "# TYPE django_cache_healthy gauge",
                    "django_cache_healthy 0",
                    "",
                ])
            
        except Exception as e:
            lines.extend([
                f"# ERROR collecting custom metrics: {str(e)}",
                "",
            ])
        
        return "\n".join(lines)


class SystemStatusView(APIView):
    """
    Detailed system status endpoint for administrative monitoring.
    
    Provides comprehensive system information for debugging and monitoring.
    """
    
    permission_classes = [AllowAny]  # May want to restrict this in production
    
    def get(self, request):
        """
        Return detailed system status information.
        
        Returns:
            Response: JSON response with comprehensive system status
        """
        try:
            status_info = {
                "system": self._get_system_info(),
                "database": self._get_database_status(),
                "cache": self._get_cache_status(),
                "application": self._get_application_status(),
                "performance": self._get_performance_metrics(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            return Response(status_info)
            
        except Exception as e:
            logger.error("Failed to collect system status", error=str(e))
            return Response({
                "error": "Failed to collect system status",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_system_info(self):
        """Get basic system information."""
        import os
        import sys
        import platform
        
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "hostname": platform.node(),
            "process_id": os.getpid(),
            "working_directory": os.getcwd(),
            "environment": getattr(settings, "DJANGO_ENV", "unknown"),
            "debug_mode": getattr(settings, "DEBUG", False),
        }
    
    def _get_database_status(self):
        """Get database connection status and info."""
        try:
            db_conn = connections["default"]
            
            # Test connection
            start_time = time.time()
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                db_version = cursor.fetchone()[0] if cursor.rowcount > 0 else "unknown"
            connection_time = (time.time() - start_time) * 1000
            
            return {
                "status": "connected",
                "engine": db_conn.settings_dict.get("ENGINE", "unknown"),
                "name": db_conn.settings_dict.get("NAME", "unknown"),
                "host": db_conn.settings_dict.get("HOST", "localhost"),
                "port": db_conn.settings_dict.get("PORT", "unknown"),
                "version": db_version,
                "connection_time_ms": round(connection_time, 2),
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def _get_cache_status(self):
        """Get cache status and configuration."""
        try:
            cache_config = getattr(settings, "CACHES", {}).get("default", {})
            
            # Test cache operation
            start_time = time.time()
            test_key = f"status_test_{int(time.time())}"
            cache.set(test_key, "test_value", timeout=10)
            cached_value = cache.get(test_key)
            cache.delete(test_key)
            operation_time = (time.time() - start_time) * 1000
            
            return {
                "status": "working" if cached_value == "test_value" else "error",
                "backend": cache_config.get("BACKEND", "unknown"),
                "location": cache_config.get("LOCATION", "unknown"),
                "operation_time_ms": round(operation_time, 2),
                "configuration": {
                    k: v for k, v in cache_config.items() 
                    if k not in ["OPTIONS"]  # Hide sensitive options
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def _get_application_status(self):
        """Get Django application status."""
        return {
            "installed_apps": len(getattr(settings, "INSTALLED_APPS", [])),
            "middleware": len(getattr(settings, "MIDDLEWARE", [])),
            "time_zone": getattr(settings, "TIME_ZONE", "unknown"),
            "language_code": getattr(settings, "LANGUAGE_CODE", "unknown"),
            "allowed_hosts": getattr(settings, "ALLOWED_HOSTS", []),
            "version_info": getattr(settings, "VERSION_INFO", {}),
        }
    
    def _get_performance_metrics(self):
        """Get basic performance metrics."""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            
            return {
                "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "uptime_seconds": round(time.time() - process.create_time(), 2),
            }
            
        except ImportError:
            # psutil not available
            return {
                "note": "psutil not installed - limited performance metrics available"
            }
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
            }