from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Service listings
    path('', views.ServiceListView.as_view(), name='service_list'),
    path('<slug:slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('category/<slug:slug>/', views.ServiceCategoryListView.as_view(), name='category_list'),
    
    # Course related
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:course_id>/enroll/', views.enroll_in_course, name='enroll_course'),
    
    # Task management
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:task_id>/apply/', views.apply_for_task, name='apply_task'),
    
    # Reviews
    path('<int:service_id>/review/', views.submit_review, name='submit_review'),
    
    # User enrollments
    path('my-enrollments/', views.my_enrollments, name='my_enrollments'),
    
    # Search and stats
    path('api/search/', views.service_search, name='service_search'),
    path('stats/', views.ServiceStatsView.as_view(), name='service_stats'),
]