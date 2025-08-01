from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import ServiceCategory, Service, ServiceReview


class ServiceCategorySerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color', 'parent',
            'is_active', 'order', 'services_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    @extend_schema_field(serializers.IntegerField())
    def get_services_count(self, obj) -> int:
        return obj.services.filter(is_active=True).count()


class ServiceListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'category_name', 'description', 'service_type',
            'featured_image', 'price', 'discount_price', 'duration_weeks',
            'difficulty_level', 'is_featured', 'created_at'
        ]


class ServiceDetailSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'slug', 'category', 'description', 'detailed_description',
            'service_type', 'difficulty_level', 'featured_image', 'video_url',
            'price', 'discount_price', 'currency', 'duration_weeks', 'max_participants',
            'prerequisites', 'required_tools', 'is_featured', 'is_active',
            'average_rating', 'created_at', 'updated_at'
        ]


class ServiceReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ServiceReview
        fields = [
            'id', 'user_name', 'rating', 'title', 'comment',
            'is_verified', 'created_at'
        ]
        read_only_fields = ['user_name', 'is_verified', 'created_at']
