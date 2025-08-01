from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ServiceCategoryViewSet, ServiceViewSet, ServiceReviewViewSet

app_name = 'services'

# API Router - using main API views
router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'reviews', ServiceReviewViewSet, basename='service-review')

urlpatterns = [
    # Services API endpoints
    path('', include(router.urls)),
]