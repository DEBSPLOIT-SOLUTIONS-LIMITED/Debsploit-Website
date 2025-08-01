from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db import models
from .models import BlogCategory, BlogPost, BlogComment, BlogTag, Newsletter, ContactMessage
from .serializers import (
    BlogCategorySerializer, BlogPostListSerializer, BlogPostDetailSerializer,
    BlogPostCreateUpdateSerializer, BlogCommentSerializer, BlogTagSerializer,
    NewsletterSerializer, ContactMessageSerializer
)


class BlogCategoryViewSet(viewsets.ModelViewSet):
    queryset = BlogCategory.objects.filter(is_active=True)
    serializer_class = BlogCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class BlogTagViewSet(viewsets.ModelViewSet):
    queryset = BlogTag.objects.all()
    serializer_class = BlogTagSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class BlogPostViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'author', 'status', 'is_featured']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['created_at', 'published_date', 'views_count', 'title']
    ordering = ['-published_date', '-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BlogPost.objects.all()
        return BlogPost.objects.filter(status='published')

    def get_serializer_class(self):
        if self.action == 'list':
            return BlogPostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BlogPostCreateUpdateSerializer
        return BlogPostDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured blog posts"""
        featured_posts = BlogPost.objects.filter(status='published', is_featured=True)[:5]
        serializer = BlogPostListSerializer(featured_posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent blog posts"""
        recent_posts = BlogPost.objects.filter(status='published').order_by('-published_date')[:10]
        serializer = BlogPostListSerializer(recent_posts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def publish(self, request, pk=None):
        """Publish a blog post"""
        post = self.get_object()
        post.status = 'published'
        if not post.published_date:
            post.published_date = timezone.now()
        post.save()
        return Response({'message': 'Post published successfully'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def unpublish(self, request, pk=None):
        """Unpublish a blog post"""
        post = self.get_object()
        post.status = 'draft'
        post.save()
        return Response({'message': 'Post unpublished successfully'})


class BlogCommentViewSet(viewsets.ModelViewSet):
    serializer_class = BlogCommentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['post', 'is_approved']
    ordering = ['created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BlogComment.objects.all()
        elif user.is_authenticated:
            # Users can see approved comments and their own comments
            return BlogComment.objects.filter(
                models.Q(is_approved=True) | models.Q(author=user)
            )
        return BlogComment.objects.filter(is_approved=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a comment"""
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        return Response({'message': 'Comment approved successfully'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a comment"""
        comment = self.get_object()
        comment.is_approved = False
        comment.save()
        return Response({'message': 'Comment rejected successfully'})


class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['email', 'name']
    ordering_fields = ['subscribed_date', 'email']
    ordering = ['-subscribed_date']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def subscribe(self, request):
        """Subscribe to newsletter"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Successfully subscribed to newsletter'}, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe from newsletter"""
        try:
            newsletter = self.get_object()
            newsletter.is_active = False
            newsletter.save()
            return Response({'message': 'Successfully unsubscribed from newsletter'})
        except Newsletter.DoesNotExist:
            return Response({'error': 'Subscription not found'}, 
                          status=status.HTTP_404_NOT_FOUND)


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['subject', 'status']
    search_fields = ['name', 'email', 'message']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def mark_in_progress(self, request, pk=None):
        """Mark message as in progress"""
        message = self.get_object()
        message.status = 'in_progress'
        message.save()
        return Response({'message': 'Message marked as in progress'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def mark_resolved(self, request, pk=None):
        """Mark message as resolved"""
        message = self.get_object()
        message.status = 'resolved'
        message.save()
        return Response({'message': 'Message marked as resolved'})
