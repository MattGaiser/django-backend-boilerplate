"""
URL configuration for API v1.

Defines all endpoints for version 1 of the API with proper routing
and viewset registration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.v1.views.auth import (
    auth_status,
    obtain_auth_token,
    refresh_auth_token,
    revoke_auth_token,
    token_info,
)
from api.v1.views.demo import LoggingDemoView
from api.v1.views.flow_trigger import trigger_hello_world_flow
from api.v1.views.health import HealthCheckView, LivenessProbeView, ReadinessProbeView
from api.v1.views.metrics import MetricsView, PrometheusMetricsView, SystemStatusView
from api.v1.views.storage import (
    storage_upload,
    storage_download,
    storage_delete,
    storage_list,
    storage_info,
    storage_usage,
)
from api.v1.views.user import PublicUserViewSet, UserViewSet
from api.v1.views.version import version_info
from api.views import api_root

# Create the main router for v1 API
router = DefaultRouter()

# Register viewsets
router.register(r"users", UserViewSet, basename="users")
router.register(r"public/users", PublicUserViewSet, basename="public-users")

# URL patterns for v1 API
urlpatterns = [
    # API discovery endpoint
    path("", api_root, name="api-root"),
    # System endpoints
    path("version/", version_info, name="api-version"),
    path("health/", HealthCheckView.as_view(), name="api-health-check"),
    path("health/live/", LivenessProbeView.as_view(), name="api-liveness-probe"),
    path("health/ready/", ReadinessProbeView.as_view(), name="api-readiness-probe"),
    # Monitoring and metrics endpoints
    path("metrics/", MetricsView.as_view(), name="api-metrics"),
    path("metrics/prometheus/", PrometheusMetricsView.as_view(), name="api-prometheus-metrics"),
    path("system/status/", SystemStatusView.as_view(), name="api-system-status"),
    # Demo endpoints
    path("demo/logging/", LoggingDemoView.as_view(), name="api-logging-demo"),
    # Authentication endpoints
    path("auth/token/", obtain_auth_token, name="api-token-auth"),
    path("auth/revoke-token/", revoke_auth_token, name="api-token-revoke"),
    path("auth/refresh-token/", refresh_auth_token, name="api-token-refresh"),
    path("auth/token-info/", token_info, name="api-token-info"),
    path("auth/status/", auth_status, name="api-auth-status"),
    # Flow trigger endpoints
    path("flows/test-run/", trigger_hello_world_flow, name="trigger-hello-world-flow"),
    # Storage endpoints
    path("storage/upload/", storage_upload, name="storage-upload"),
    path("storage/download/<path:file_path>/", storage_download, name="storage-download"),
    path("storage/delete/<path:file_path>/", storage_delete, name="storage-delete"),
    path("storage/list/", storage_list, name="storage-list"),
    path("storage/info/<path:file_path>/", storage_info, name="storage-info"),
    path("storage/usage/", storage_usage, name="storage-usage"),
    # Include router URLs
    path("", include(router.urls)),
]
