"""
URL configuration for config project.

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
from django.contrib import admin
from django.urls import path, include
from health.views import health_check, readiness_check
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Health checks (for Docker, load balancers, monitoring)
    path("health/", health_check, name="health-check"),
    path("ready/", readiness_check, name="readiness-check"),

    # Admin
    path("admin/", admin.site.urls),

    # API Documentation (OpenAPI 3.0)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # API endpoints
    path("api/auth/", include("users.urls")),
    path("api/", include("personas.urls")),
    path("api/", include("debates.urls")),
    path("api/", include("texts.urls")),
    path("api/payments/", include("payments.urls")),
]
