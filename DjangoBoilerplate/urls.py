"""
URL configuration for DjangoBoilerplate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core.demo_views import LoggingDemoView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.v1.urls")),
    path("accounts/", include("allauth.urls")),
    path("demo/logging/", LoggingDemoView.as_view(), name="logging-demo"),
]

# Add API documentation URLs
if "drf_spectacular" in settings.INSTALLED_APPS:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularRedocView,
        SpectacularSwaggerView,
    )
    
    urlpatterns += [
        # API schema and documentation
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]

# Add Prometheus metrics endpoint  
if "django_prometheus" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("metrics/", include("django_prometheus.urls")),
    ]

# Development-only URLs
if settings.DEBUG:
    # Debug toolbar
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [
            path("__debug__/", include("debug_toolbar.urls")),
        ]
    
    # Silk profiling
    if "silk" in settings.INSTALLED_APPS:
        urlpatterns += [
            path("silk/", include("silk.urls", namespace="silk")),
        ]
