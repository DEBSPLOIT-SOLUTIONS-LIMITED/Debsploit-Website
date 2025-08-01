from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import ServiceCategory, Service, ServiceReview


@extend_schema_view(
    list=extend_schema(description="List all service categories"),
    retrieve=extend_schema(description="Get a specific service category"),
    create=extend_schema(description="Create a new service category"),
    update=extend_schema(description="Update a service category"),
    destroy=extend_schema(description="Delete a service category"),
)
class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_serializer_class(self):
        from .serializers import ServiceCategorySerializer
        return ServiceCategorySerializer

    @extend_schema(description="Get root categories (no parent)")
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get root categories (no parent)"""
        root_categories = ServiceCategory.objects.filter(parent=None, is_active=True).order_by('order', 'name')
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="List all services"),
    retrieve=extend_schema(description="Get a specific service"),
    create=extend_schema(description="Create a new service"),
    update=extend_schema(description="Update a service"),
    destroy=extend_schema(description="Delete a service"),
)
class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'difficulty_level', 'service_type', 'is_featured']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return Service.objects.filter(is_active=True)

    def get_serializer_class(self):
        from .serializers import ServiceListSerializer, ServiceDetailSerializer
        if self.action == 'list':
            return ServiceListSerializer
        return ServiceDetailSerializer

    @extend_schema(description="Get featured services")
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured services"""
        featured_services = Service.objects.filter(is_active=True, is_featured=True)[:6]
        from .serializers import ServiceListSerializer
        serializer = ServiceListSerializer(featured_services, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="List all service reviews"),
    retrieve=extend_schema(description="Get a specific service review"),
    create=extend_schema(description="Create a new service review"),
    update=extend_schema(description="Update a service review"),
    destroy=extend_schema(description="Delete a service review"),
)
class ServiceReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service', 'rating', 'is_verified']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ServiceReview.objects.none()
        return ServiceReview.objects.filter(is_verified=True)

    def get_serializer_class(self):
        from .serializers import ServiceReviewSerializer
        return ServiceReviewSerializer
