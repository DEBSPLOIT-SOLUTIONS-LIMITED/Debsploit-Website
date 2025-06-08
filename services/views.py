from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import (
    Service, ServiceCategory, Course, Enrollment, Task, TaskApplication,
    TaskSubmission, ServiceReview, CompanyInfo
)
from .forms import (
    ServiceReviewForm, TaskApplicationForm, TaskSubmissionForm,
    EnrollmentForm, ServiceSearchForm
)
from accounts.models import UserNotification, UserAchievement
from dashboard.models import UserActivity

class ServiceListView(ListView):
    """List all services with filtering and search"""
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True).select_related('category')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by service type
        service_type = self.request.GET.get('type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        # Filter by difficulty level
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['price', '-price', 'title', '-title', 'created_at', '-created_at', '-average_rating']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter options
        context['categories'] = ServiceCategory.objects.filter(is_active=True)
        context['service_types'] = Service.SERVICE_TYPES
        context['difficulty_levels'] = Service.DIFFICULTY_LEVELS
        
        # Current filters
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'category': self.request.GET.get('category', ''),
            'type': self.request.GET.get('type', ''),
            'difficulty': self.request.GET.get('difficulty', ''),
            'min_price': self.request.GET.get('min_price', ''),
            'max_price': self.request.GET.get('max_price', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        
        # Featured services
        context['featured_services'] = Service.objects.filter(
            is_active=True, is_featured=True
        )[:3]
        
        return context

class ServiceDetailView(DetailView):
    """Detailed view of a service"""
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    
    def get_queryset(self):
        return Service.objects.filter(is_active=True).select_related('category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        
        # Related course
        try:
            context['course'] = Course.objects.get(service=service)
        except Course.DoesNotExist:
            context['course'] = None
        
        # User enrollment status
        if self.request.user.is_authenticated:
            context['user_enrollment'] = Enrollment.objects.filter(
                user=self.request.user,
                course__service=service
            ).first()
        
        # Service reviews
        reviews = ServiceReview.objects.filter(
            service=service, is_verified=True
        ).select_related('user').order_by('-created_at')
        context['reviews'] = reviews[:10]
        context['reviews_count'] = reviews.count()
        
        # Average rating breakdown
        rating_counts = reviews.values('rating').annotate(count=Count('rating'))
        context['rating_breakdown'] = {r['rating']: r['count'] for r in rating_counts}
        
        # Related services
        context['related_services'] = Service.objects.filter(
            category=service.category,
            is_active=True
        ).exclude(id=service.id)[:4]
        
        # Review form (for enrolled users)
        if (self.request.user.is_authenticated and 
            context.get('user_enrollment') and 
            not reviews.filter(user=self.request.user).exists()):
            context['review_form'] = ServiceReviewForm()
        
        return context

class CourseDetailView(DetailView):
    """Detailed view of a course"""
    model = Course
    template_name = 'services/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # User enrollment status
        if self.request.user.is_authenticated:
            context['user_enrollment'] = Enrollment.objects.filter(
                user=self.request.user,
                course=course
            ).first()
        
        # Course statistics
        context['enrollment_stats'] = {
            'current_enrollment': course.current_enrollment,
            'max_participants': course.service.max_participants,
            'enrollment_percentage': course.enrollment_percentage,
            'is_full': course.is_full,
        }
        
        # Enrolled students (for instructor/admin)
        if (self.request.user.is_authenticated and 
            (self.request.user == course.instructor or self.request.user.is_staff)):
            context['enrolled_students'] = Enrollment.objects.filter(
                course=course
            ).select_related('user').order_by('-enrolled_date')
        
        return context

@login_required
def enroll_in_course(request, course_id):
    """Enroll user in a course"""
    course = get_object_or_404(Course, id=course_id, service__is_active=True)
    
    # Check if user is already enrolled
    existing_enrollment = Enrollment.objects.filter(
        user=request.user,
        course=course
    ).first()
    
    if existing_enrollment:
        messages.warning(request, f'You are already enrolled in {course.service.title}.')
        return redirect('services:course_detail', pk=course.id)
    
    # Check if course is full
    if course.is_full:
        messages.error(request, 'This course is currently full.')
        return redirect('services:course_detail', pk=course.id)
    
    # Check if enrollment is open
    if not course.is_enrollment_open:
        messages.error(request, 'Enrollment for this course is currently closed.')
        return redirect('services:course_detail', pk=course.id)
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        user=request.user,
        course=course,
        amount_paid=course.service.effective_price
    )
    
    # Update course enrollment count
    course.current_enrollment += 1
    course.save()
    
    # Create notification
    UserNotification.objects.create(
        user=request.user,
        title='Course Enrollment Successful',
        message=f'You have successfully enrolled in {course.service.title}.',
        notification_type='course_enrolled'
    )
    
    # Award points for enrollment
    request.user.add_points(20)
    
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='course_enrollment',
        description=f'Enrolled in course: {course.service.title}'
    )
    
    # Send confirmation email
    send_enrollment_confirmation_email(request.user, course)
    
    messages.success(request, f'Successfully enrolled in {course.service.title}!')
    return redirect('dashboard:courses')

class TaskListView(ListView):
    """List available tasks for developers"""
    model = Task
    template_name = 'services/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Task.objects.select_related('assigned_by').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status', 'open')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by task type
        task_type = self.request.GET.get('type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Budget range filter
        min_budget = self.request.GET.get('min_budget')
        max_budget = self.request.GET.get('max_budget')
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(requirements__icontains=search_query)
            )
        
        # Sort
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['budget', '-budget', 'due_date', '-due_date', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter options
        context['task_types'] = Task.TASK_TYPES
        context['priority_levels'] = Task.PRIORITY_LEVELS
        context['status_choices'] = Task.STATUS_CHOICES
        
        # Current filters
        context['current_filters'] = {
            'status': self.request.GET.get('status', 'open'),
            'type': self.request.GET.get('type', ''),
            'priority': self.request.GET.get('priority', ''),
            'min_budget': self.request.GET.get('min_budget', ''),
            'max_budget': self.request.GET.get('max_budget', ''),
            'search': self.request.GET.get('search', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        
        # Statistics
        context['stats'] = {
            'total_tasks': Task.objects.count(),
            'open_tasks': Task.objects.filter(status='open').count(),
            'my_applications': 0,
            'my_assigned_tasks': 0,
        }
        
        if self.request.user.is_authenticated and self.request.user.user_type == 'developer':
            context['stats']['my_applications'] = TaskApplication.objects.filter(
                applicant=self.request.user
            ).count()
            context['stats']['my_assigned_tasks'] = Task.objects.filter(
                assigned_to=self.request.user
            ).count()
        
        return context

class TaskDetailView(DetailView):
    """Detailed view of a task"""
    model = Task
    template_name = 'services/task_detail.html'
    context_object_name = 'task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        user = self.request.user
        
        # Check if user has applied
        if user.is_authenticated and user.user_type == 'developer':
            context['user_application'] = TaskApplication.objects.filter(
                task=task,
                applicant=user
            ).first()
            
            context['can_apply'] = (
                task.status == 'open' and
                task.assigned_to != user and
                not context['user_application']
            )
        
        # Task applications (for task owner/admin)
        if user.is_authenticated and (user == task.assigned_by or user.is_staff):
            context['applications'] = TaskApplication.objects.filter(
                task=task
            ).select_related('applicant').order_by('-applied_date')
        
        # Task submission (for assigned developer)
        if task.assigned_to == user:
            context['task_submission'] = TaskSubmission.objects.filter(
                task=task
            ).first()
        
        # Related tasks
        context['related_tasks'] = Task.objects.filter(
            task_type=task.task_type,
            status='open'
        ).exclude(id=task.id)[:5]
        
        return context

@login_required
def apply_for_task(request, task_id):
    """Apply for a task"""
    task = get_object_or_404(Task, id=task_id, status='open')
    
    # Check if user is a developer
    if request.user.user_type != 'developer':
        messages.error(request, 'Only developers can apply for tasks.')
        return redirect('services:task_detail', pk=task.id)
    
    # Check if user has already applied
    existing_application = TaskApplication.objects.filter(
        task=task,
        applicant=request.user
    ).first()
    
    if existing_application:
        messages.warning(request, 'You have already applied for this task.')
        return redirect('services:task_detail', pk=task.id)
    
    if request.method == 'POST':
        form = TaskApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.task = task
            application.applicant = request.user
            application.save()
            
            # Notify task owner
            UserNotification.objects.create(
                user=task.assigned_by,
                title='New Task Application',
                message=f'{request.user.get_full_name()} applied for task: {task.title}',
                notification_type='task_assigned'
            )
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='task_application',
                description=f'Applied for task: {task.title}'
            )
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('services:task_detail', pk=task.id)
    else:
        form = TaskApplicationForm()
    
    context = {
        'task': task,
        'form': form,
    }
    return render(request, 'services/task_application.html', context)

@login_required
@require_http_methods(["POST"])
def submit_review(request, service_id):
    """Submit a service review"""
    service = get_object_or_404(Service, id=service_id, is_active=True)
    
    # Check if user is enrolled in the service
    enrollment = Enrollment.objects.filter(
        user=request.user,
        course__service=service
    ).first()
    
    if not enrollment:
        return JsonResponse({
            'success': False,
            'error': 'You must be enrolled to review this service.'
        })
    
    # Check if user has already reviewed
    existing_review = ServiceReview.objects.filter(
        service=service,
        user=request.user
    ).first()
    
    if existing_review:
        return JsonResponse({
            'success': False,
            'error': 'You have already reviewed this service.'
        })
    
    form = ServiceReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.service = service
        review.user = request.user
        review.save()
        
        # Update service average rating
        avg_rating = ServiceReview.objects.filter(
            service=service,
            is_verified=True
        ).aggregate(avg=Avg('rating'))['avg']
        
        service.average_rating = avg_rating or 0
        service.save()
        
        # Award points for review
        request.user.add_points(10)
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='review_posted',
            description=f'Reviewed service: {service.title}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully!',
            'review': {
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment,
                'user_name': review.user.get_full_name(),
                'created_at': review.created_at.strftime('%B %d, %Y'),
            }
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    })

class ServiceCategoryListView(ListView):
    """List services by category"""
    model = Service
    template_name = 'services/category_list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(
            ServiceCategory,
            slug=self.kwargs['slug'],
            is_active=True
        )
        return Service.objects.filter(
            category=self.category,
            is_active=True
        ).order_by('-is_featured', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['all_categories'] = ServiceCategory.objects.filter(is_active=True)
        return context

@login_required
def my_enrollments(request):
    """Display user's enrollments"""
    enrollments = Enrollment.objects.filter(
        user=request.user
    ).select_related('course__service', 'course__instructor').order_by('-enrolled_date')
    
    # Pagination
    paginator = Paginator(enrollments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_enrolled': enrollments.count(),
        'active_courses': enrollments.filter(status='active').count(),
        'completed_courses': enrollments.filter(status='completed').count(),
        'total_points_earned': enrollments.aggregate(
            total=Sum('points_earned')
        )['total'] or 0,
    }
    
    context = {
        'enrollments': page_obj,
        'stats': stats,
    }
    return render(request, 'services/my_enrollments.html', context)

def service_search(request):
    """AJAX service search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    services = Service.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True
    )[:10]
    
    results = [
        {
            'id': service.id,
            'title': service.title,
            'description': service.description[:100] + '...' if len(service.description) > 100 else service.description,
            'category': service.category.name,
            'price': str(service.effective_price),
            'currency': service.currency,
            'url': service.get_absolute_url(),
            'image': service.featured_image.url if service.featured_image else None,
        }
        for service in services
    ]
    
    return JsonResponse({'results': results})

def send_enrollment_confirmation_email(user, course):
    """Send enrollment confirmation email"""
    try:
        subject = f'Enrollment Confirmation - {course.service.title}'
        
        html_message = render_to_string('emails/enrollment_confirmation.html', {
            'user': user,
            'course': course,
            'service': course.service,
            'dashboard_url': f"{settings.SITE_URL}/dashboard/courses/",
        })
        
        send_mail(
            subject=subject,
            message=f'You have successfully enrolled in {course.service.title}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send enrollment confirmation email: {e}")

# Additional utility views
class ServiceStatsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Service statistics for admins"""
    model = Service
    template_name = 'services/service_stats.html'
    context_object_name = 'services'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Overall statistics
        context['stats'] = {
            'total_services': Service.objects.filter(is_active=True).count(),
            'total_enrollments': Enrollment.objects.count(),
            'total_revenue': Enrollment.objects.aggregate(
                total=Sum('amount_paid')
            )['total'] or 0,
            'average_rating': Service.objects.filter(
                is_active=True
            ).aggregate(avg=Avg('average_rating'))['avg'] or 0,
        }
        
        # Top performing services
        context['top_services'] = Service.objects.filter(
            is_active=True
        ).annotate(
            enrollment_count=Count('course__enrollments')
        ).order_by('-enrollment_count')[:10]
        
        # Recent enrollments
        context['recent_enrollments'] = Enrollment.objects.select_related(
            'user', 'course__service'
        ).order_by('-enrolled_date')[:10]
        
        return context