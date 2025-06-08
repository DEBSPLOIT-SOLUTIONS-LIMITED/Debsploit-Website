from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard pages
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('tasks/', views.TasksView.as_view(), name='tasks'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:task_id>/apply/', views.TaskApplicationCreateView.as_view(), name='task_apply'),
    path('portfolio/', views.PortfolioView.as_view(), name='portfolio'),
    path('notifications/', views.NotificationsView.as_view(), name='notifications'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    
    # AJAX API endpoints
    path('api/notifications/', views.api_notifications, name='api_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/progress/update/', views.update_user_progress, name='update_user_progress'),
    path('api/applications/<int:application_id>/accept/', views.accept_task_application, name='accept_task_application'),
    
    # Data export
    path('export/user-data/', views.export_user_data, name='export_user_data'),
]