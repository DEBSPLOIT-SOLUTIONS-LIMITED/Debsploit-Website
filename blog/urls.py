from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    BlogCategoryViewSet, BlogPostViewSet, BlogCommentViewSet, 
    BlogTagViewSet, NewsletterViewSet, ContactMessageViewSet
)

app_name = 'blog'

# API Router
router = DefaultRouter()
router.register(r'categories', BlogCategoryViewSet, basename='category')
router.register(r'posts', BlogPostViewSet, basename='post')
router.register(r'comments', BlogCommentViewSet, basename='comment')
router.register(r'tags', BlogTagViewSet, basename='tag')
router.register(r'newsletter', NewsletterViewSet, basename='newsletter')
router.register(r'contact', ContactMessageViewSet, basename='contact')

urlpatterns = [
    # Blog API endpoints
    path('', include(router.urls)),
]