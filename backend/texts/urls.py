"""
URL routing for Primary Text API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrimaryTextViewSet, TextSectionViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'texts', PrimaryTextViewSet, basename='text')
router.register(r'sections', TextSectionViewSet, basename='section')

urlpatterns = [
    path('', include(router.urls)),
]
