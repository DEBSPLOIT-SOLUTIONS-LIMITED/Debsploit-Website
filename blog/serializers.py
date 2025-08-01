from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from typing import List, Dict, Any
from .models import BlogCategory, BlogPost, BlogComment, BlogTag, Newsletter, ContactMessage
from accounts.serializers import UserListSerializer


class BlogCategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'slug', 'description', 'color', 'is_active', 'posts_count', 'created_at']
        read_only_fields = ['slug', 'created_at']
    
    @extend_schema_field(serializers.IntegerField())
    def get_posts_count(self, obj) -> int:
        return obj.posts.filter(status='published').count()


class BlogTagSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogTag
        fields = ['id', 'name', 'slug', 'posts_count', 'created_at']
        read_only_fields = ['slug', 'created_at']
    
    @extend_schema_field(serializers.IntegerField())
    def get_posts_count(self, obj) -> int:
        return obj.posts.filter(status='published').count()


class BlogCommentSerializer(serializers.ModelSerializer):
    author = UserListSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogComment
        fields = [
            'id', 'author', 'content', 'is_approved', 'created_at', 
            'updated_at', 'parent', 'replies'
        ]
        read_only_fields = ['author', 'is_approved', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_replies(self, obj) -> List[Dict[str, Any]]:
        if obj.replies.exists():
            return BlogCommentSerializer(obj.replies.filter(is_approved=True), many=True).data
        return []


class BlogPostListSerializer(serializers.ModelSerializer):
    author = UserListSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'excerpt', 'featured_image',
            'status', 'is_featured', 'views_count', 'reading_time', 'tags',
            'comments_count', 'published_date', 'created_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.IntegerField())
    def get_comments_count(self, obj) -> int:
        return obj.comments.filter(is_approved=True).count()


class BlogPostDetailSerializer(serializers.ModelSerializer):
    author = UserListSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'excerpt', 'content',
            'featured_image', 'meta_description', 'meta_keywords', 'status',
            'is_featured', 'allow_comments', 'views_count', 'reading_time',
            'tags', 'comments', 'comments_count', 'published_date', 
            'created_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_comments(self, obj) -> List[Dict[str, Any]]:
        # Only return top-level comments (replies are nested in BlogCommentSerializer)
        comments = obj.comments.filter(is_approved=True, parent=None).order_by('created_at')
        return BlogCommentSerializer(comments, many=True).data
    
    @extend_schema_field(serializers.IntegerField())
    def get_comments_count(self, obj) -> int:
        return obj.comments.filter(is_approved=True).count()


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=BlogTag.objects.all(), required=False)
    
    class Meta:
        model = BlogPost
        fields = [
            'title', 'category', 'excerpt', 'content', 'featured_image',
            'meta_description', 'meta_keywords', 'status', 'is_featured',
            'allow_comments', 'tags', 'published_date'
        ]
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = BlogPost.objects.create(**validated_data)
        post.tags.set(tags)
        return post
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['id', 'email', 'name', 'is_active', 'subscribed_date']
        read_only_fields = ['subscribed_date']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'phone', 'subject', 'message', 'status',
            'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'admin_notes', 'created_at', 'updated_at']
