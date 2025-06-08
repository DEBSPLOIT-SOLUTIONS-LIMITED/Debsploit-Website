from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

from accounts.models import User, UserNotification, UserAchievement, UserSkill
from services.models import (
    Service, Task, TaskApplication, TaskSubmission, Enrollment, 
    Course, ServiceReview
)
from blog.models import BlogPost
from .models import (
    UserProgress, ProjectPortfolio, LearningPath, UserLearningPath,
    DeveloperProfile, DashboardAnalytics, UserActivity
)
from .forms import (
    UserProfileForm, DeveloperProfileForm, ProjectPortfolioForm,
    TaskApplicationForm, TaskSubmissionForm, UserSkillForm
)

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create user progress
        progress, created = UserProgress.objects.get_or_create(user=user)
        
        # Recent activity
        recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
        
        # User statistics
        stats = {
            'total_points': user.points,
            'courses_enrolled': Enrollment.objects.filter(user=user).count(),
            'courses_completed': Enrollment.objects.filter(
                user=user, status='completed'
            ).count(),
            'tasks_assigned': Task.objects.filter(assigned_to=user).count(),
            'tasks_completed': Task.objects.filter(
                assigned_to=user, status='completed'
            ).count(),
            'achievements_earned': UserAchievement.objects.filter(user=user).count(),
            'portfolio_projects': ProjectPortfolio.objects.filter(user=user).count(),
        }
        
        # Recent enrollments
        recent_enrollments = Enrollment.objects.filter(user=user).order_by('-enrolled_date')[:5]
        
        # Recent tasks (for developers)
        recent_tasks = []
        if user.user_type == 'developer':
            recent_tasks = Task.objects.filter(
                Q(assigned_to=user) | Q(applications__applicant=user)
            ).distinct().order_by('-created_at')[:5]
        
        # Recent achievements
        recent_achievements = UserAchievement.objects.filter(user=user).order_by('-earned_date')[:5]
        
        # Notifications
        unread_notifications = UserNotification.objects.filter(
            user=user, is_read=False
        ).order_by('-created_at')[:5]
        
        # Learning paths
        user_learning_paths = UserLearningPath.objects.filter(
            user=user, is_active=True
        ).select_related('learning_path')
        
        # Quick actions based on user type
        quick_actions = self.get_quick_actions(user)
        
        # Upcoming deadlines
        upcoming_deadlines = []
        if user.user_type == 'developer':
            upcoming_deadlines = Task.objects.filter(
                assigned_to=user,
                status__in=['assigned', 'in_progress'],
                due_date__gte=timezone.now(),
                due_date__lte=timezone.now() + timedelta(days=7)
            ).order_by('due_date')
        
        context.update({
            'progress': progress,
            'stats': stats,
            'recent_activities': recent_activities,
            'recent_enrollments': recent_enrollments,
            'recent_tasks': recent_tasks,
            'recent_achievements': recent_achievements,
            'unread_notifications': unread_notifications,
            'user_learning_paths': user_learning_paths,
            'quick_actions': quick_actions,
            'upcoming_deadlines': upcoming_deadlines,
        })
        
        return context
    
    def get_quick_actions(self, user):
        """Get quick action buttons based on user type"""
        actions = [
            {
                'title': 'Browse Courses',
                'url': '/services/?type=training',
                'icon': 'fas fa-graduation-cap',
                'color': 'primary'
            },
            {
                'title': 'View Profile',
                'url': '/dashboard/profile/',
                'icon': 'fas fa-user',
                'color': 'secondary'
            },
        ]
        
        if user.user_type == 'developer':
            actions.extend([
                {
                    'title': 'Browse Tasks',
                    'url': '/dashboard/tasks/',
                    'icon': 'fas fa-tasks',
                    'color': 'success'
                },
                {
                    'title': 'My Portfolio',
                    'url': '/dashboard/portfolio/',
                    'icon': 'fas fa-briefcase',
                    'color': 'info'
                },
            ])
        
        if user.user_type == 'instructor':
            actions.extend([
                {
                    'title': 'My Courses',
                    'url': '/dashboard/instructor/courses/',
                    'icon': 'fas fa-chalkboard-teacher',
                    'color': 'warning'
                },
                {
                    'title': 'Create Content',
                    'url': '/blog/create/',
                    'icon': 'fas fa-edit',
                    'color': 'info'
                },
            ])
        
        return actions

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'dashboard/profile.html'
    success_url = '/dashboard/profile/'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User skills
        user_skills = UserSkill.objects.filter(user=user)
        
        # User achievements
        achievements = UserAchievement.objects.filter(user=user).order_by('-earned_date')
        
        # Developer profile for developers
        developer_profile = None
        if user.user_type == 'developer':
            developer_profile, created = DeveloperProfile.objects.get_or_create(user=user)
        
        context.update({
            'user_skills': user_skills,
            'achievements': achievements,
            'developer_profile': developer_profile,
        })
        
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description='Profile information updated'
        )
        
        return super().form_valid(form)

class CoursesView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/courses.html'
    context_object_name = 'enrollments'
    paginate_by = 12
    
    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related(
            'course__service', 'course__instructor'
        ).order_by('-enrolled_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Course statistics
        enrollments = Enrollment.objects.filter(user=user)
        stats = {
            'total_enrolled': enrollments.count(),
            'active_courses': enrollments.filter(status='active').count(),
            'completed_courses': enrollments.filter(status='completed').count(),
            'pending_courses': enrollments.filter(status='pending').count(),
        }
        
        # Available courses (not enrolled)
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        available_courses = Course.objects.filter(
            service__is_active=True,
            is_enrollment_open=True
        ).exclude(id__in=enrolled_course_ids)[:6]
        
        # Learning paths
        learning_paths = LearningPath.objects.filter(is_active=True)[:4]
        
        context.update({
            'stats': stats,
            'available_courses': available_courses,
            'learning_paths': learning_paths,
        })
        
        return context

class TasksView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/tasks.html'
    context_object_name = 'tasks'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow developers to access this view
        if request.user.user_type != 'developer':
            messages.warning(request, 'This section is only available for developers.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        filter_type = self.request.GET.get('filter', 'assigned')
        
        if filter_type == 'assigned':
            return Task.objects.filter(assigned_to=user).order_by('-created_at')
        elif filter_type == 'applied':
            applied_task_ids = TaskApplication.objects.filter(
                applicant=user
            ).values_list('task_id', flat=True)
            return Task.objects.filter(id__in=applied_task_ids).order_by('-created_at')
        elif filter_type == 'available':
            return Task.objects.filter(
                status='open',
                assigned_to__isnull=True
            ).order_by('-created_at')
        else:
            return Task.objects.filter(
                Q(assigned_to=user) | Q(applications__applicant=user)
            ).distinct().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Task statistics
        stats = {
            'assigned_tasks': Task.objects.filter(assigned_to=user).count(),
            'completed_tasks': Task.objects.filter(
                assigned_to=user, status='completed'
            ).count(),
            'in_progress_tasks': Task.objects.filter(
                assigned_to=user, status='in_progress'
            ).count(),
            'applied_tasks': TaskApplication.objects.filter(applicant=user).count(),
        }
        
        # Current filter
        current_filter = self.request.GET.get('filter', 'assigned')
        
        # Recent applications
        recent_applications = TaskApplication.objects.filter(
            applicant=user
        ).select_related('task').order_by('-applied_date')[:5]
        
        context.update({
            'stats': stats,
            'current_filter': current_filter,
            'recent_applications': recent_applications,
        })
        
        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'dashboard/task_detail.html'
    context_object_name = 'task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        task = self.object
        
        # Check if user has applied
        user_application = None
        if user.user_type == 'developer':
            try:
                user_application = TaskApplication.objects.get(
                    task=task, applicant=user
                )
            except TaskApplication.DoesNotExist:
                pass
        
        # Check if user can apply
        can_apply = (
            user.user_type == 'developer' and
            task.status == 'open' and
            task.assigned_to != user and
            user_application is None
        )
        
        # Get task submission if exists
        task_submission = None
        if task.assigned_to == user:
            try:
                task_submission = TaskSubmission.objects.get(task=task)
            except TaskSubmission.DoesNotExist:
                pass
        
        # All applications for this task (for task owner/admin)
        applications = None
        if user == task.assigned_by or user.is_staff:
            applications = TaskApplication.objects.filter(
                task=task
            ).select_related('applicant').order_by('-applied_date')
        
        context.update({
            'user_application': user_application,
            'can_apply': can_apply,
            'task_submission': task_submission,
            'applications': applications,
        })
        
        return context

class TaskApplicationCreateView(LoginRequiredMixin, CreateView):
    model = TaskApplication
    form_class = TaskApplicationForm
    template_name = 'dashboard/task_application.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type != 'developer':
            return HttpResponseForbidden("Only developers can apply for tasks.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task'] = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return context
    
    def form_valid(self, form):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        
        # Check if user can apply
        if (task.status != 'open' or 
            TaskApplication.objects.filter(task=task, applicant=self.request.user).exists()):
            messages.error(self.request, 'You cannot apply for this task.')
            return redirect('dashboard:task_detail', pk=task.pk)
        
        form.instance.task = task
        form.instance.applicant = self.request.user
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='task_application',
            description=f'Applied for task: {task.title}'
        )
        
        messages.success(self.request, 'Application submitted successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return f'/dashboard/tasks/{self.kwargs["task_id"]}/'

class PortfolioView(LoginRequiredMixin, ListView):
    model = ProjectPortfolio
    template_name = 'dashboard/portfolio.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        return ProjectPortfolio.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Portfolio statistics
        projects = ProjectPortfolio.objects.filter(user=user)
        stats = {
            'total_projects': projects.count(),
            'completed_projects': projects.filter(status='completed').count(),
            'in_progress_projects': projects.filter(status='in_progress').count(),
            'featured_projects': projects.filter(is_featured=True).count(),
        }
        
        # Project types breakdown
        project_types = projects.values('project_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context.update({
            'stats': stats,
            'project_types': project_types,
        })
        
        return context

class NotificationsView(LoginRequiredMixin, ListView):
    model = UserNotification
    template_name = 'dashboard/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mark notifications as read when viewed
        UserNotification.objects.filter(
            user=self.request.user, is_read=False
        ).update(is_read=True)
        
        # Notification statistics
        notifications = UserNotification.objects.filter(user=self.request.user)
        stats = {
            'total_notifications': notifications.count(),
            'unread_notifications': notifications.filter(is_read=False).count(),
            'today_notifications': notifications.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }
        
        context.update({
            'stats': stats,
        })
        
        return context

class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/analytics.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only allow admin users
        if not request.user.is_staff:
            messages.warning(request, 'Access denied.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range (last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # User analytics
        user_stats = {
            'total_users': User.objects.count(),
            'new_users_this_month': User.objects.filter(
                date_joined__date__gte=start_date
            ).count(),
            'active_users': User.objects.filter(
                last_login__date__gte=start_date
            ).count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
        }
        
        # User type breakdown
        user_types = User.objects.values('user_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Task analytics
        task_stats = {
            'total_tasks': Task.objects.count(),
            'open_tasks': Task.objects.filter(status='open').count(),
            'in_progress_tasks': Task.objects.filter(status='in_progress').count(),
            'completed_tasks': Task.objects.filter(status='completed').count(),
        }
        
        # Service analytics
        service_stats = {
            'total_services': Service.objects.filter(is_active=True).count(),
            'total_enrollments': Enrollment.objects.count(),
            'active_enrollments': Enrollment.objects.filter(status='active').count(),
            'completed_enrollments': Enrollment.objects.filter(status='completed').count(),
        }
        
        # Recent activity
        recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:20]
        
        # Dashboard analytics
        dashboard_analytics = DashboardAnalytics.objects.filter(
            date__gte=start_date
        ).order_by('-date')[:30]
        
        context.update({
            'user_stats': user_stats,
            'user_types': user_types,
            'task_stats': task_stats,
            'service_stats': service_stats,
            'recent_activities': recent_activities,
            'dashboard_analytics': dashboard_analytics,
            'date_range': f"{start_date} to {end_date}",
        })
        
        return context

# AJAX Views
@login_required
@require_http_methods(["GET"])
def api_notifications(request):
    """API endpoint for loading notifications"""
    notifications = UserNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'notification_type': n.notification_type,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = UserNotification.objects.get(
            id=notification_id, user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except UserNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    UserNotification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_user_progress(request):
    """Update user progress via AJAX"""
    try:
        data = json.loads(request.body)
        skill_area = data.get('skill_area')
        progress_value = int(data.get('progress', 0))
        
        if progress_value < 0 or progress_value > 100:
            return JsonResponse({'success': False, 'error': 'Invalid progress value'})
        
        progress, created = UserProgress.objects.get_or_create(user=request.user)
        
        # Update the specific skill area
        if hasattr(progress, f'{skill_area}_level'):
            setattr(progress, f'{skill_area}_level', progress_value)
            progress.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='progress_update',
                description=f'Updated {skill_area} progress to {progress_value}%'
            )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid skill area'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def accept_task_application(request, application_id):
    """Accept a task application (for task owners)"""
    try:
        application = TaskApplication.objects.get(id=application_id)
        task = application.task
        
        # Check permissions
        if request.user != task.assigned_by and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        # Accept the application
        application.status = 'accepted'
        application.reviewed_date = timezone.now()
        application.reviewed_by = request.user
        application.save()
        
        # Assign the task
        task.assigned_to = application.applicant
        task.status = 'assigned'
        task.assigned_date = timezone.now()
        task.save()
        
        # Reject other applications
        TaskApplication.objects.filter(
            task=task
        ).exclude(id=application_id).update(
            status='rejected',
            reviewed_date=timezone.now(),
            reviewed_by=request.user
        )
        
        # Create notification for the developer
        UserNotification.objects.create(
            user=application.applicant,
            title='Task Assigned',
            message=f'You have been assigned the task: {task.title}',
            notification_type='task_assigned'
        )
        
        # Log activity
        UserActivity.objects.create(
            user=application.applicant,
            activity_type='task_assigned',
            description=f'Assigned to task: {task.title}'
        )
        
        return JsonResponse({'success': True})
        
    except TaskApplication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def export_user_data(request):
    """Export user data (GDPR compliance)"""
    user = request.user
    
    # Collect user data
    user_data = {
        'personal_info': {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'phone': str(user.phone) if user.phone else None,
            'bio': user.bio,
            'date_joined': user.date_joined.isoformat(),
            'points': user.points,
        },
        'enrollments': [
            {
                'course': e.course.service.title,
                'status': e.status,
                'enrolled_date': e.enrolled_date.isoformat(),
                'progress': e.progress_percentage,
            }
            for e in Enrollment.objects.filter(user=user)
        ],
        'tasks': [
            {
                'title': t.title,
                'status': t.status,
                'assigned_date': t.assigned_date.isoformat() if t.assigned_date else None,
            }
            for t in Task.objects.filter(assigned_to=user)
        ],
        'achievements': [
            {
                'title': a.title,
                'description': a.description,
                'earned_date': a.earned_date.isoformat(),
                'points': a.points_awarded,
            }
            for a in UserAchievement.objects.filter(user=user)
        ],
        'activities': [
            {
                'activity_type': a.activity_type,
                'description': a.description,
                'timestamp': a.timestamp.isoformat(),
            }
            for a in UserActivity.objects.filter(user=user).order_by('-timestamp')[:100]
        ],
    }
    
    response = JsonResponse(user_data, indent=2)
    response['Content-Disposition'] = f'attachment; filename="user_data_{user.id}.json"'
    return response