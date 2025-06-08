from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('team/', views.TeamView.as_view(), name='team'),
    
    # Dynamic pages
    path('page/<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
    
    # Search
    path('search/', views.search_view, name='search'),
    
    # AJAX endpoints
    path('api/newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
    path('api/update-analytics/', views.update_analytics, name='update_analytics'),
    
    # SEO
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    path('robots.txt', views.robots_txt_view, name='robots_txt'),
]