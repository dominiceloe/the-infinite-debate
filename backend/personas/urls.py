from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PersonaViewSet, PersonaRequestViewSet

router = DefaultRouter()
router.register(r'personas', PersonaViewSet, basename='persona')
router.register(r'persona-requests', PersonaRequestViewSet, basename='persona-request')

urlpatterns = router.urls
