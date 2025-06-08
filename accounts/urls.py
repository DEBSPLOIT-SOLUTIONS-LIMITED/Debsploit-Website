from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Profile views
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name='user_profile'),
    path('public/<str:username>/', views.user_public_profile, name='public_profile'),
    
    # User management
    path('users/', views.UserListView.as_view(), name='user_list'),
    
    # Skills management
    path('skills/', views.UserSkillsView.as_view(), name='user_skills'),
    path('skills/add/', views.add_user_skill, name='add_user_skill'),
    path('skills/<int:skill_id>/remove/', views.remove_user_skill, name='remove_user_skill'),
    
    # Achievements
    path('achievements/', views.UserAchievementsView.as_view(), name='achievements'),
    path('achievements/<int:user_pk>/', views.UserAchievementsView.as_view(), name='user_achievements'),
    
    # Notifications
    path('notifications/', views.user_notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Data management
    path('export-data/', views.export_user_data, name='export_user_data'),
    path('delete-account/', views.delete_account, name='delete_account'),
]