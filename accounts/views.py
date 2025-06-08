from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, CreateView, ListView
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, UserSkill, UserAchievement, UserNotification
from .forms import (
    CustomUserCreationForm, UserProfileForm, UserSkillForm,
    UserSearchForm, ContactAdminForm
)
from dashboard.models import UserActivity

User = get_user_model()

class UserProfileView(LoginRequiredMixin, DetailView):
    """Display user profile"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        # If no pk provided, show current user's profile
        if 'pk' in self.kwargs:
            return get_object_or_404(User, pk=self.kwargs['pk'])
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        
        # User skills grouped by category
        skills_by_category = {}
        skills = UserSkill.objects.filter(user=profile_user).order_by('category', 'name')
        for skill in skills:
            category = skill.get_category_display()
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)
        
        # User achievements
        achievements = UserAchievement.objects.filter(user=profile_user).order_by('-earned_date')[:10]
        
        # Recent activity (only for own profile or admin)
        recent_activity = []
        if profile_user == self.request.user or self.request.user.is_staff:
            recent_activity = UserActivity.objects.filter(
                user=profile_user
            ).order_by('-timestamp')[:10]
        
        # Portfolio projects (if developer)
        portfolio_projects = []
        if profile_user.user_type == 'developer':
            from dashboard.models import ProjectPortfolio
            portfolio_projects = ProjectPortfolio.objects.filter(
                user=profile_user,
                is_public=True
            ).order_by('-is_featured', '-created_at')[:6]
        
        # Statistics
        stats = {
            'total_skills': skills.count(),
            'verified_skills': skills.filter(is_verified=True).count(),
            'total_achievements': achievements.count(),
            'total_points': profile_user.points,
            'member_since': profile_user.date_joined,
        }
        
        # Additional stats for developers
        if profile_user.user_type == 'developer':
            from services.models import Task, TaskApplication
            dev_stats = {
                'tasks_completed': Task.objects.filter(
                    assigned_to=profile_user, status='completed'
                ).count(),
                'tasks_in_progress': Task.objects.filter(
                    assigned_to=profile_user, status='in_progress'
                ).count(),
                'applications_sent': TaskApplication.objects.filter(
                    applicant=profile_user
                ).count(),
                'portfolio_projects': portfolio_projects.count(),
            }
            stats.update(dev_stats)
        
        context.update({
            'skills_by_category': skills_by_category,
            'achievements': achievements,
            'recent_activity': recent_activity,
            'portfolio_projects': portfolio_projects,
            'stats': stats,
            'is_own_profile': profile_user == self.request.user,
        })
        
        return context

class UserListView(ListView):
    """List all users with search and filtering"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True).select_related()
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(company__icontains=search_query) |
                Q(job_title__icontains=search_query)
            )
        
        # Filter by user type
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Filter by verification status
        verified = self.request.GET.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified=True)
        elif verified == 'false':
            queryset = queryset.filter(is_verified=False)
        
        # Filter by country
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country=country)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-date_joined')
        if sort_by in ['date_joined', '-date_joined', 'points', '-points', 'first_name', '-first_name']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Current filters
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'user_type': self.request.GET.get('user_type', ''),
            'verified': self.request.GET.get('verified', ''),
            'country': self.request.GET.get('country', ''),
            'sort': self.request.GET.get('sort', '-date_joined'),
        }
        
        # Filter options
        context['user_types'] = User.USER_TYPES
        context['countries'] = User.objects.values_list('country', flat=True).distinct()
        
        # Statistics
        context['stats'] = {
            'total_users': User.objects.filter(is_active=True).count(),
            'verified_users': User.objects.filter(is_active=True, is_verified=True).count(),
            'developers': User.objects.filter(user_type='developer', is_active=True).count(),
            'students': User.objects.filter(user_type='student', is_active=True).count(),
        }
        
        return context

class UserSkillsView(LoginRequiredMixin, ListView):
    """Manage user skills"""
    model = UserSkill
    template_name = 'accounts/user_skills.html'
    context_object_name = 'skills'
    
    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user).order_by('category', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group skills by category
        skills_by_category = {}
        for skill in context['skills']:
            category = skill.get_category_display()
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)
        
        context['skills_by_category'] = skills_by_category
        context['skill_form'] = UserSkillForm()
        
        return context

@login_required
@require_http_methods(["POST"])
def add_user_skill(request):
    """Add a new skill to user profile"""
    form = UserSkillForm(request.POST, user=request.user)
    
    if form.is_valid():
        # Check if skill already exists
        existing_skill = UserSkill.objects.filter(
            user=request.user,
            name__iexact=form.cleaned_data['name']
        ).first()
        
        if existing_skill:
            return JsonResponse({
                'success': False,
                'error': 'You already have this skill in your profile.'
            })
        
        skill = form.save()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='profile_update',
            description=f'Added skill: {skill.name}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Skill added successfully!',
            'skill': {
                'id': skill.id,
                'name': skill.name,
                'category': skill.get_category_display(),
                'proficiency': skill.get_proficiency_display(),
                'years_experience': skill.years_experience,
                'is_verified': skill.is_verified,
            }
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    })

@login_required
@require_http_methods(["POST"])
def remove_user_skill(request, skill_id):
    """Remove a skill from user profile"""
    try:
        skill = UserSkill.objects.get(id=skill_id, user=request.user)
        skill_name = skill.name
        skill.delete()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='profile_update',
            description=f'Removed skill: {skill_name}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Skill removed successfully!'
        })
    except UserSkill.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Skill not found.'
        })

class UserAchievementsView(LoginRequiredMixin, ListView):
    """Display user achievements"""
    model = UserAchievement
    template_name = 'accounts/achievements.html'
    context_object_name = 'achievements'
    paginate_by = 20
    
    def get_queryset(self):
        user_pk = self.kwargs.get('user_pk')
        if user_pk:
            user = get_object_or_404(User, pk=user_pk)
        else:
            user = self.request.user
        
        return UserAchievement.objects.filter(user=user).order_by('-earned_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_pk = self.kwargs.get('user_pk')
        if user_pk:
            context['profile_user'] = get_object_or_404(User, pk=user_pk)
        else:
            context['profile_user'] = self.request.user
        
        # Achievement statistics
        achievements = context['achievements']
        context['stats'] = {
            'total_achievements': achievements.count(),
            'total_points_from_achievements': sum(a.points_awarded for a in achievements),
            'recent_achievements': achievements[:5],
            'achievement_types': achievements.values('achievement_type').annotate(
                count=Count('id')
            ).order_by('-count'),
        }
        
        return context

@login_required
def user_notifications(request):
    """Display user notifications"""
    notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark notifications as read when viewed
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'unread_count': unread_notifications.count(),
    }
    
    return render(request, 'accounts/notifications.html', context)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = UserNotification.objects.get(
            id=notification_id,
            user=request.user
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
    UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def export_user_data(request):
    """Export user data for GDPR compliance"""
    user = request.user
    
    # Collect all user data
    user_data = {
        'personal_information': {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'phone': str(user.phone) if user.phone else None,
            'bio': user.bio,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'country': str(user.country) if user.country else None,
            'city': user.city,
            'address': user.address,
            'company': user.company,
            'job_title': user.job_title,
            'experience_years': user.experience_years,
            'skill_level': user.skill_level,
            'points': user.points,
            'is_verified': user.is_verified,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'skills': [
            {
                'name': skill.name,
                'category': skill.category,
                'proficiency': skill.proficiency,
                'years_experience': skill.years_experience,
                'is_verified': skill.is_verified,
                'created_at': skill.created_at.isoformat(),
            }
            for skill in UserSkill.objects.filter(user=user)
        ],
        'achievements': [
            {
                'title': achievement.title,
                'description': achievement.description,
                'achievement_type': achievement.achievement_type,
                'points_awarded': achievement.points_awarded,
                'earned_date': achievement.earned_date.isoformat(),
            }
            for achievement in UserAchievement.objects.filter(user=user)
        ],
        'notifications': [
            {
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
            }
            for notification in UserNotification.objects.filter(user=user).order_by('-created_at')[:100]
        ],
        'activity': [
            {
                'activity_type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.timestamp.isoformat(),
            }
            for activity in UserActivity.objects.filter(user=user).order_by('-timestamp')[:100]
        ],
    }
    
    # Add enrollments data
    from services.models import Enrollment
    user_data['enrollments'] = [
        {
            'course': enrollment.course.service.title,
            'status': enrollment.status,
            'enrolled_date': enrollment.enrolled_date.isoformat(),
            'progress_percentage': enrollment.progress_percentage,
            'completion_date': enrollment.completion_date.isoformat() if enrollment.completion_date else None,
            'points_earned': enrollment.points_earned,
        }
        for enrollment in Enrollment.objects.filter(user=user)
    ]
    
    # Add tasks data (for developers)
    if user.user_type == 'developer':
        from services.models import Task, TaskApplication
        user_data['tasks'] = [
            {
                'title': task.title,
                'status': task.status,
                'assigned_date': task.assigned_date.isoformat() if task.assigned_date else None,
                'due_date': task.due_date.isoformat(),
                'completed_date': task.completed_date.isoformat() if task.completed_date else None,
                'budget': str(task.budget),
                'points_reward': task.points_reward,
            }
            for task in Task.objects.filter(assigned_to=user)
        ]
        
        user_data['task_applications'] = [
            {
                'task_title': app.task.title,
                'status': app.status,
                'applied_date': app.applied_date.isoformat(),
                'cover_letter': app.cover_letter,
                'proposed_budget': str(app.proposed_budget) if app.proposed_budget else None,
            }
            for app in TaskApplication.objects.filter(applicant=user)
        ]
    
    response = JsonResponse(user_data, indent=2)
    response['Content-Disposition'] = f'attachment; filename="user_data_{user.id}_{timezone.now().date()}.json"'
    return response

@login_required
def delete_account(request):
    """Handle account deletion request"""
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Verify password
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password. Account not deleted.')
            return redirect('accounts:profile')
        
        # Log the deletion
        UserActivity.objects.create(
            user=request.user,
            activity_type='account_deletion',
            description='User requested account deletion'
        )
        
        # Mark user as inactive instead of deleting (for data integrity)
        user = request.user
        user.is_active = False
        user.email = f"deleted_{user.id}_{user.email}"
        user.save()
        
        messages.success(request, 'Your account has been deactivated successfully.')
        return redirect('core:home')
    
    return render(request, 'accounts/delete_account.html')

# API Views
@login_required
@require_http_methods(["GET"])
def api_user_stats(request):
    """API endpoint for user statistics"""
    user = request.user
    
    stats = {
        'points': user.points,
        'achievements_count': UserAchievement.objects.filter(user=user).count(),
        'skills_count': UserSkill.objects.filter(user=user).count(),
        'notifications_count': UserNotification.objects.filter(user=user, is_read=False).count(),
    }
    
    # Add type-specific stats
    if user.user_type == 'developer':
        from services.models import Task, TaskApplication
        stats.update({
            'tasks_assigned': Task.objects.filter(assigned_to=user).count(),
            'tasks_completed': Task.objects.filter(assigned_to=user, status='completed').count(),
            'applications_sent': TaskApplication.objects.filter(applicant=user).count(),
        })
    elif user.user_type == 'student':
        from services.models import Enrollment
        stats.update({
            'courses_enrolled': Enrollment.objects.filter(user=user).count(),
            'courses_completed': Enrollment.objects.filter(user=user, status='completed').count(),
        })
    
    return JsonResponse(stats)

@login_required
@require_http_methods(["GET"])
def api_user_activity(request):
    """API endpoint for user activity feed"""
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:20]
    
    activity_data = [
        {
            'id': activity.id,
            'activity_type': activity.activity_type,
            'description': activity.description,
            'timestamp': activity.timestamp.isoformat(),
            'time_ago': activity.timestamp,
        }
        for activity in activities
    ]
    
    return JsonResponse({'activities': activity_data})

def user_public_profile(request, username):
    """Public user profile view"""
    user = get_object_or_404(User, username=username, is_active=True)
    
    # Only show public information
    context = {
        'profile_user': user,
        'public_skills': UserSkill.objects.filter(user=user, is_verified=True),
        'public_achievements': UserAchievement.objects.filter(user=user)[:10],
        'is_public_view': True,
    }
    
    # Add portfolio for developers
    if user.user_type == 'developer':
        from dashboard.models import ProjectPortfolio
        context['portfolio_projects'] = ProjectPortfolio.objects.filter(
            user=user,
            is_public=True
        ).order_by('-is_featured', '-created_at')[:6]
    
    return render(request, 'accounts/public_profile.html', context)