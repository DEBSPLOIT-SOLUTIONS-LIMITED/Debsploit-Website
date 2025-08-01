from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# API Schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Debsploit Solutions API",
        default_version='v1',
        description="API for Debsploit Solutions platform providing cybersecurity training, programming courses, and various IT services.",
        terms_of_service="https://www.debsploitsolutions.com/terms/",
        contact=openapi.Contact(email="contact@debsploitsolutions.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Alternative Swagger/ReDoc with drf-yasg
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API endpoints
    path('api/v1/', include('accounts.urls')),
    path('api/v1/', include('services.urls')),
    path('api/v1/', include('blog.urls')),
    path('api/v1/', include('dashboard.urls')),
    path('api/v1/', include('core.urls')),
    
    # Custom Admin UI
    path('', include('admin_ui.urls')),
    
    # Auth (keep for admin and custom UI)
    path('accounts/', include('allauth.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
]

# Development-only URLs
if settings.DEBUG:
    # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        
        pass

# Admin customization
admin.site.site_header = "Debsploit Solutions Admin"
admin.site.site_title = "Debsploit Admin Portal"
admin.site.index_title = "Welcome to Debsploit Solutions Administration"