from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

app_name = 'core'

class APIInfoResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    version = serializers.CharField()
    description = serializers.CharField()
    endpoints = serializers.DictField()

@extend_schema(
    responses={200: APIInfoResponseSerializer},
    description="Get API information and available endpoints"
)
@api_view(['GET'])
def api_info(request):
    """API endpoint for core information"""
    return Response({
        'name': 'Debsploit Solutions API',
        'version': '1.0.0',
        'description': 'API for Debsploit Solutions platform',
        'endpoints': {
            'users': '/api/v1/users/',
            'services': '/api/v1/services/',
            'blog': '/api/v1/posts/',
            'docs': '/api/docs/',
            'redoc': '/api/redoc/'
        }
    })

urlpatterns = [
    # Core API endpoints
    path('info/', api_info, name='api_info'),
]