"""
URL configuration for API v1.

Defines all endpoints for version 1 of the API with proper routing
and viewset registration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Import existing views
from api.v1.views.auth import (
    auth_status,
    obtain_auth_token,
    refresh_auth_token,
    revoke_auth_token,
    token_info,
)
from api.v1.views.demo import LoggingDemoView
from api.v1.views.flow_trigger import trigger_hello_world_flow
from api.v1.views.health import HealthCheckView
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

# Import new auth views
from api.v1.views.auth_new import (
    signup,
    signin,
    signout,
    session,
    refresh_token as new_refresh_token,
    token_info as new_token_info,
)

# Import organization and project views
from api.v1.views.organization import (
    OrganizationViewSet,
    OrganizationMembershipViewSet,
    ProjectViewSet,
    PublicProjectViewSet,
)

# Import evidence views
from api.v1.views.evidence import (
    EvidenceSourceViewSet,
    EvidenceFactViewSet,
    EvidenceChunkViewSet,
    EvidenceInsightViewSet,
    RecommendationViewSet,
)

# Import tag views
from api.v1.views.tags import (
    TagViewSet,
    TagSummaryViewSet,
    PublicTagViewSet,
)

# Import function views
from api.v1.views.functions import (
    search_similar_facts,
    debug_auth_context,
    process_document,
    ai_conversation,
    generate_insights,
    generate_recommendations,
)

# Import storage views
from api.v1.views.storage_new import (
    upload_evidence_file,
    download_evidence_file,
    delete_evidence_file,
    list_evidence_files,
    get_file_info,
    get_storage_usage,
    create_signed_upload_url,
    create_signed_download_url,
)

# Create the main router for v1 API
router = DefaultRouter()

# Register existing viewsets
router.register(r"users", UserViewSet, basename="users")
router.register(r"public/users", PublicUserViewSet, basename="public-users")

# Register new viewsets
router.register(r"organizations", OrganizationViewSet, basename="organizations")
router.register(r"organization-memberships", OrganizationMembershipViewSet, basename="organization-memberships")
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"public/projects", PublicProjectViewSet, basename="public-projects")

router.register(r"evidence-sources", EvidenceSourceViewSet, basename="evidence-sources")
router.register(r"evidence-facts", EvidenceFactViewSet, basename="evidence-facts")
router.register(r"evidence-chunks", EvidenceChunkViewSet, basename="evidence-chunks")
router.register(r"evidence-insights", EvidenceInsightViewSet, basename="evidence-insights")
router.register(r"recommendations", RecommendationViewSet, basename="recommendations")

router.register(r"tags", TagSummaryViewSet, basename="tags")
router.register(r"tags-detail", TagViewSet, basename="tags-detail")
router.register(r"public/tags", PublicTagViewSet, basename="public-tags")

# URL patterns for v1 API
urlpatterns = [
    # API discovery endpoint
    path("", api_root, name="api-root"),
    
    # System endpoints
    path("version/", version_info, name="api-version"),
    path("health/", HealthCheckView.as_view(), name="api-health-check"),
    
    # Demo endpoints
    path("demo/logging/", LoggingDemoView.as_view(), name="api-logging-demo"),
    
    # Authentication endpoints (existing)
    path("auth/token/", obtain_auth_token, name="api-token-auth"),
    path("auth/revoke-token/", revoke_auth_token, name="api-token-revoke"),
    path("auth/refresh-token/", refresh_auth_token, name="api-token-refresh"),
    path("auth/token-info/", token_info, name="api-token-info"),
    path("auth/status/", auth_status, name="api-auth-status"),
    
    # New authentication endpoints (Supabase-style)
    path("auth/signup/", signup, name="auth-signup"),
    path("auth/signin/", signin, name="auth-signin"),
    path("auth/signout/", signout, name="auth-signout"),
    path("auth/session/", session, name="auth-session"),
    path("auth/refresh-token-new/", new_refresh_token, name="auth-refresh-token-new"),
    path("auth/token-info-new/", new_token_info, name="auth-token-info-new"),
    
    # RPC endpoints (matching Supabase /rest/v1/rpc/ pattern)
    path("rpc/search-similar-facts/", search_similar_facts, name="rpc-search-similar-facts"),
    path("rpc/debug-auth-context/", debug_auth_context, name="rpc-debug-auth-context"),
    
    # Function endpoints (matching Supabase /functions/v1/ pattern)
    path("functions/process-document/", process_document, name="functions-process-document"),
    path("functions/ai-conversation/", ai_conversation, name="functions-ai-conversation"),
    path("functions/generate-insights/", generate_insights, name="functions-generate-insights"),
    path("functions/generate-recommendations/", generate_recommendations, name="functions-generate-recommendations"),
    
    # Storage endpoints (existing)
    path("storage/upload/", storage_upload, name="storage-upload"),
    path("storage/download/<path:file_path>/", storage_download, name="storage-download"),
    path("storage/delete/<path:file_path>/", storage_delete, name="storage-delete"),
    path("storage/list/", storage_list, name="storage-list"),
    path("storage/info/<path:file_path>/", storage_info, name="storage-info"),
    path("storage/usage/", storage_usage, name="storage-usage"),
    
    # New storage endpoints (matching Supabase /storage/v1/ pattern)
    path("storage/evidence-files/upload/", upload_evidence_file, name="storage-evidence-upload"),
    path("storage/evidence-files/list/", list_evidence_files, name="storage-evidence-list"),
    path("storage/evidence-files/usage/", get_storage_usage, name="storage-evidence-usage"),
    path("storage/evidence-files/<path:file_path>/", download_evidence_file, name="storage-evidence-download"),
    path("storage/evidence-files/<path:file_path>/delete/", delete_evidence_file, name="storage-evidence-delete"),
    path("storage/evidence-files/<path:file_path>/info/", get_file_info, name="storage-evidence-info"),
    path("storage/signed-upload-url/", create_signed_upload_url, name="storage-signed-upload"),
    path("storage/signed-download-url/", create_signed_download_url, name="storage-signed-download"),
    
    # Flow trigger endpoints
    path("flows/test-run/", trigger_hello_world_flow, name="trigger-hello-world-flow"),
    
    # Include router URLs
    path("", include(router.urls)),
]
