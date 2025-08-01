from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import UserViewSet, CustomTokenObtainPairView

app_name = 'accounts'

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT Authentication
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User API endpoints
    path('', include(router.urls)),
]