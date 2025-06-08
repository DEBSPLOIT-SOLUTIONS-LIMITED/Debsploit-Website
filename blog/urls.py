from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Blog post views
    path('', views.BlogPostListView.as_view(), name='post_list'),
    path('post/<slug:slug>/', views.BlogPostDetailView.as_view(), name='post_detail'),
    path('create/', views.BlogPostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/edit/', views.BlogPostUpdateView.as_view(), name='post_update'),
    path('post/<slug:slug>/delete/', views.BlogPostDeleteView.as_view(), name='post_delete'),
    
    # Category and tag views
    path('category/<slug:slug>/', views.BlogCategoryView.as_view(), name='category_posts'),
    path('tag/<slug:slug>/', views.BlogTagView.as_view(), name='tag_posts'),
    
    # Author posts
    path('author/<int:author_id>/', views.author_posts, name='author_posts'),
    
    # Archive
    path('archive/', views.archive_view, name='archive'),
    
    # Comments
    path('post/<slug:post_slug>/comment/', views.add_comment, name='add_comment'),
    
    # Contact and newsletter
    path('contact/', views.contact_view, name='contact'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    
    # Testimonials
    path('testimonials/', views.TestimonialListView.as_view(), name='testimonials'),
    
    # Search
    path('api/search/', views.blog_search, name='blog_search'),
]