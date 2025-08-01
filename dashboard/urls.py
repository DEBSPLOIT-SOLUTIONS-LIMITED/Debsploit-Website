from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

app_name = 'dashboard'

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    # You can implement this later with actual dashboard data
    return Response({'message': 'Dashboard API endpoint'})

urlpatterns = [
    # Dashboard API endpoints
    path('stats/', dashboard_stats, name='stats'),
]