"""
URL configuration for API v1.

Defines all endpoints for version 1 of the API with proper routing
and viewset registration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.v1.views.user import UserViewSet, PublicUserViewSet
from api.v1.views.auth import (
    obtain_auth_token,
    revoke_auth_token, 
    refresh_auth_token,
    token_info
)

# Create the main router for v1 API
router = DefaultRouter()

# Register viewsets
router.register(r'users', UserViewSet, basename='users')
router.register(r'public/users', PublicUserViewSet, basename='public-users')

# URL patterns for v1 API
urlpatterns = [
    # Authentication endpoints
    path('auth/token/', obtain_auth_token, name='api-token-auth'),
    path('auth/revoke-token/', revoke_auth_token, name='api-token-revoke'),
    path('auth/refresh-token/', refresh_auth_token, name='api-token-refresh'),
    path('auth/token-info/', token_info, name='api-token-info'),
    
    # Include router URLs
    path('', include(router.urls)),
]