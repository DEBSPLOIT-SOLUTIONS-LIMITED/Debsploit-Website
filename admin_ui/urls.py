from django.urls import path
from . import views

app_name = 'admin_ui'

urlpatterns = [
    # Admin dashboard
    path('', views.admin_dashboard, name='dashboard'),
    path('users/', views.admin_users, name='users'),
    path('services/', views.admin_services, name='services'),
    path('blog/', views.admin_blog, name='blog'),
    path('contacts/', views.admin_contacts, name='contacts'),
    path('settings/', views.admin_settings, name='settings'),
]
