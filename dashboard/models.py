from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Sum, Count
from datetime import datetime, timedelta
import json

User = get_user_model()

class DashboardAnalytics(models.Model):
    """Store analytics data for dashboard metrics"""
    date = models.DateField(default=timezone.now, unique=True)
    
    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    new_users_today = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    verified_users = models.PositiveIntegerField(default=0)
    students_count = models.PositiveIntegerField(default=0)
    developers_count = models.PositiveIntegerField(default=0)
    instructors_count = models.PositiveIntegerField(default=0)
    
    # Service metrics
    total_enrollments = models.PositiveIntegerField(default=0)
    new_enrollments_today = models.PositiveIntegerField(default=0)
    completed_courses = models.PositiveIntegerField(default=0)
    active_courses = models.PositiveIntegerField(default=0)
    
    # Task metrics
    total_tasks = models.PositiveIntegerField(default=0)
    open_tasks = models.PositiveIntegerField(default=0)
    in_progress_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    cancelled_tasks = models.PositiveIntegerField(default=0)
    
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    revenue_today = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Content metrics
    total_blog_posts = models.PositiveIntegerField(default=0)
    published_posts = models.PositiveIntegerField(default=0)
    draft_posts = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    approved_comments = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    newsletter_subscribers = models.PositiveIntegerField(default=0)
    new_subscribers_today = models.PositiveIntegerField(default=0)
    contact_messages = models.PositiveIntegerField(default=0)
    testimonials_received = models.PositiveIntegerField(default=0)
    
    # System metrics
    page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_session_duration = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Dashboard Analytics"
    
    def __str__(self):
        return f"Analytics for {self.date}"
    
    @classmethod
    def get_analytics_for_period(cls, days=30):
        """Get analytics for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        return cls.objects.filter(date__range=[start_date, end_date]).order_by('date')

class UserActivity(models.Model):
    """Track user activities for analytics and audit"""
    ACTIVITY_TYPES = (
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('profile_update', 'Profile Updated'),
        ('password_change', 'Password Changed'),
        ('course_enrollment', 'Course Enrollment'),
        ('course_completion', 'Course Completion'),
        ('task_application', 'Task Application'),
        ('task_assigned', 'Task Assigned'),
        ('task_submission', 'Task Submission'),
        ('task_completion', 'Task Completion'),
        ('blog_post', 'Blog Post Created/Updated'),
        ('comment', 'Comment Posted'),
        ('review_posted', 'Review Posted'),
        ('achievement_earned', 'Achievement Earned'),
        ('points_earned', 'Points Earned'),
        ('skill_added', 'Skill Added'),
        ('portfolio_updated', 'Portfolio Updated'),
        ('newsletter_subscription', 'Newsletter Subscription'),
        ('account_deletion', 'Account Deletion'),
        ('file_upload', 'File Uploaded'),
        ('download', 'File Downloaded'),
        ('search', 'Search Performed'),
        ('page_view', 'Page Viewed'),
        ('api_call', 'API Call Made'),
        ('email_sent', 'Email Sent'),
        ('error_occurred', 'Error Occurred'),
        ('progress_update', 'Progress Updated'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES, db_index=True)
    description = models.CharField(max_length=300)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional activity data")
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    referer = models.URLField(blank=True)
    
    # Location data
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    duration = models.DurationField(null=True, blank=True, help_text="Activity duration if applicable")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "User Activities"
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_activity_type_display()}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description, metadata=None, request=None):
        """Helper method to log user activities"""
        activity_data = {
            'user': user,
            'activity_type': activity_type,
            'description': description,
            'metadata': metadata or {},
        }
        
        if request:
            activity_data.update({
                'ip_address': cls.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'session_key': request.session.session_key,
                'referer': request.META.get('HTTP_REFERER', ''),
            })
        
        return cls.objects.create(**activity_data)
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserProgress(models.Model):
    """Track user progress across different skill areas"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    
    # Skill progress (0-100)
    programming_level = models.PositiveIntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    design_level = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    cybersecurity_level = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    networking_level = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    ai_level = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    marketing_level = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Learning metrics
    courses_completed = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    certifications_earned = models.PositiveIntegerField(default=0)
    total_study_hours = models.PositiveIntegerField(default=0)
    projects_completed = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    login_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(auto_now=True)
    total_points_earned = models.PositiveIntegerField(default=0)
    
    # Learning preferences
    preferred_learning_time = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ('night', 'Night'),
        ],
        blank=True
    )
    learning_goals = models.TextField(blank=True, help_text="User's learning objectives")
    target_completion_date = models.DateField(null=True, blank=True)
    
    # Progress tracking
    weekly_goal_hours = models.PositiveIntegerField(default=10)
    current_week_hours = models.PositiveIntegerField(default=0)
    last_week_reset = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Progress for {self.user.get_full_name()}"
    
    def get_overall_progress(self):
        """Calculate overall progress percentage"""
        skill_levels = [
            self.programming_level, self.design_level, self.cybersecurity_level,
            self.networking_level, self.ai_level, self.marketing_level
        ]
        return sum(skill_levels) // len(skill_levels) if skill_levels else 0
    
    def get_skill_breakdown(self):
        """Get skill breakdown as dictionary"""
        return {
            'Programming': self.programming_level,
            'Design': self.design_level,
            'Cybersecurity': self.cybersecurity_level,
            'Networking': self.networking_level,
            'AI/ML': self.ai_level,
            'Marketing': self.marketing_level,
        }
    
    def update_weekly_hours(self, hours):
        """Update weekly study hours and reset if needed"""
        today = timezone.now().date()
        
        # Check if we need to reset weekly hours
        if today - self.last_week_reset >= timedelta(days=7):
            self.current_week_hours = 0
            self.last_week_reset = today
        
        self.current_week_hours += hours
        self.total_study_hours += hours
        self.save()
    
    def check_weekly_goal(self):
        """Check if weekly goal is met"""
        return self.current_week_hours >= self.weekly_goal_hours

class ProjectPortfolio(models.Model):
    """User's project portfolio management"""
    PROJECT_TYPES = (
        ('web_development', 'Web Development'),
        ('mobile_app', 'Mobile Application'),
        ('desktop_app', 'Desktop Application'),
        ('data_science', 'Data Science'),
        ('ai_ml', 'AI/Machine Learning'),
        ('cybersecurity', 'Cybersecurity'),
        ('design', 'Design Project'),
        ('marketing', 'Marketing Campaign'),
        ('research', 'Research Project'),
        ('open_source', 'Open Source Contribution'),
        ('freelance', 'Freelance Project'),
        ('personal', 'Personal Project'),
        ('academic', 'Academic Project'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
        ('archived', 'Archived'),
    )
    
    DIFFICULTY_LEVELS = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_projects')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)
    
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='intermediate')
    
    # Project links and files
    github_url = models.URLField(blank=True)
    live_demo_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    project_image = models.ImageField(upload_to='portfolio_images/', blank=True)
    project_file = models.FileField(upload_to='portfolio_files/', blank=True)
    
    # Technical details
    technologies = models.TextField(help_text="Comma-separated list of technologies used")
    challenges_faced = models.TextField(blank=True, help_text="Challenges encountered and how they were solved")
    lessons_learned = models.TextField(blank=True)
    
    # Collaboration
    team_size = models.PositiveIntegerField(default=1)
    collaborators = models.ManyToManyField(User, related_name='collaborated_projects', blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    
    # Metrics
    estimated_hours = models.PositiveIntegerField(default=0)
    actual_hours = models.PositiveIntegerField(default=0)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    
    # Recognition
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    featured_on_homepage = models.BooleanField(default=False)
    
    # Visibility
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_open_source = models.BooleanField(default=False)
    
    # Awards and recognition
    awards = models.TextField(blank=True, help_text="Awards or recognition received for this project")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_public']),
            models.Index(fields=['project_type', 'status']),
            models.Index(fields=['is_featured', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
    
    def get_absolute_url(self):
        return reverse('dashboard:portfolio_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(f"{self.title}-{self.user.username}")
        super().save(*args, **kwargs)
    
    def get_technologies_list(self):
        """Return technologies as a list"""
        return [tech.strip() for tech in self.technologies.split(',') if tech.strip()]
    
    def get_progress_percentage(self):
        """Calculate project progress based on status"""
        progress_map = {
            'planning': 10,
            'in_progress': 50,
            'completed': 100,
            'on_hold': 25,
            'cancelled': 0,
            'archived': 100,
        }
        return progress_map.get(self.status, 0)
    
    def is_overdue(self):
        """Check if project is overdue"""
        if self.deadline and self.status not in ['completed', 'cancelled', 'archived']:
            return timezone.now().date() > self.deadline
        return False

class LearningPath(models.Model):
    """Predefined learning paths for different career tracks"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)
    
    # Path characteristics
    difficulty_level = models.CharField(max_length=20, choices=(
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ))
    estimated_duration_weeks = models.PositiveIntegerField()
    estimated_hours_per_week = models.PositiveIntegerField(default=10)
    
    # Visual representation
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default="#0066FF")
    cover_image = models.ImageField(upload_to='learning_paths/', blank=True)
    
    # Requirements and outcomes
    prerequisites = models.TextField(blank=True, help_text="What students need to know before starting")
    target_skills = models.TextField(help_text="Skills user will gain")
    career_outcomes = models.TextField(blank=True, help_text="Potential career paths after completion")
    
    # Curriculum structure
    modules = models.JSONField(default=list, blank=True, help_text="List of modules/sections")
    milestones = models.JSONField(default=list, blank=True, help_text="Key milestones in the path")
    
    # Related content
    services = models.ManyToManyField('services.Service', related_name='learning_paths', blank=True)
    recommended_books = models.TextField(blank=True)
    external_resources = models.TextField(blank=True)
    
    # Metrics
    enrollment_count = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('dashboard:learning_path_detail', kwargs={'slug': self.slug})
    
    def get_total_estimated_hours(self):
        """Calculate total estimated hours for the path"""
        return self.estimated_duration_weeks * self.estimated_hours_per_week

class UserLearningPath(models.Model):
    """Track user's progress through learning paths"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='user_enrollments')
    
    # Progress tracking
    started_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    last_activity_date = models.DateTimeField(auto_now=True)
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Module progress
    completed_modules = models.JSONField(default=list, blank=True)
    current_module = models.PositiveIntegerField(default=0)
    
    # Time tracking
    total_time_spent = models.DurationField(default=timedelta)
    estimated_completion_date = models.DateField(null=True, blank=True)
    
    # Engagement
    is_active = models.BooleanField(default=True)
    motivation_level = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Self-reported motivation level (1-10)"
    )
    
    # Notes and feedback
    personal_notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    class Meta:
        unique_together = ['user', 'learning_path']
        ordering = ['-started_date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.learning_path.name}"
    
    @property
    def is_completed(self):
        return self.progress_percentage >= 100 and self.completed_date is not None
    
    def mark_module_complete(self, module_index):
        """Mark a specific module as completed"""
        if module_index not in self.completed_modules:
            self.completed_modules.append(module_index)
            self.current_module = max(self.current_module, module_index + 1)
            
            # Update progress percentage
            total_modules = len(self.learning_path.modules) if self.learning_path.modules else 1
            self.progress_percentage = min(100, int((len(self.completed_modules) / total_modules) * 100))
            
            # Check if path is completed
            if self.progress_percentage >= 100 and not self.completed_date:
                self.completed_date = timezone.now()
                
                # Log completion activity
                UserActivity.objects.create(
                    user=self.user,
                    activity_type='course_completion',
                    description=f'Completed learning path: {self.learning_path.name}'
                )
            
            self.save()

class DeveloperProfile(models.Model):
    """Extended profile for developers with additional professional information"""
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable'),
    ]
    
    PROJECT_TYPE_CHOICES = [
        ('web_development', 'Web Development'),
        ('mobile_app', 'Mobile Application'),
        ('desktop_app', 'Desktop Application'),
        ('data_science', 'Data Science'),
        ('ai_ml', 'AI/Machine Learning'),
        ('cybersecurity', 'Cybersecurity'),
        ('design', 'Design Project'),
        ('marketing', 'Marketing Campaign'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='developer_profile')
    
    # Professional information matching form fields
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )
    years_of_experience = models.PositiveIntegerField(default=0)
    
    # Project preferences (supports CheckboxSelectMultiple)
    preferred_project_types = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of preferred project types"
    )
    
    # Portfolio and links matching form fields
    portfolio_website = models.URLField(blank=True)
    behance_url = models.URLField(blank=True)
    dribbble_url = models.URLField(blank=True)
    
    # Availability settings matching form fields
    is_accepting_projects = models.BooleanField(default=True)
    next_available_date = models.DateField(null=True, blank=True)
    
    # Additional professional information
    primary_skills = models.TextField(blank=True, help_text="Comma-separated list of primary skills")
    secondary_skills = models.TextField(blank=True, help_text="Comma-separated list of secondary skills")
    programming_languages = models.TextField(blank=True, help_text="Comma-separated list of programming languages")
    frameworks = models.TextField(blank=True, help_text="Comma-separated list of frameworks")
    tools = models.TextField(blank=True, help_text="Comma-separated list of tools")
    
    # Work preferences
    minimum_project_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maximum_projects_concurrent = models.PositiveIntegerField(default=3)
    work_timezone = models.CharField(max_length=50, blank=True)
    
    # Additional portfolio links
    github_username = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    resume_file = models.FileField(upload_to='resumes/', blank=True)
    
    # Performance metrics
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_projects_completed = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Settings
    is_verified = models.BooleanField(default=False)
    featured_developer = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-featured_developer', '-average_rating', '-total_projects_completed']
    
    def __str__(self):
        return f"Developer Profile - {self.user.get_full_name()}"
    
    def get_primary_skills_list(self):
        """Return primary skills as a list"""
        return [skill.strip() for skill in self.primary_skills.split(',') if skill.strip()]
    
    def get_secondary_skills_list(self):
        """Return secondary skills as a list"""
        return [skill.strip() for skill in self.secondary_skills.split(',') if skill.strip()]
    
    def get_programming_languages_list(self):
        """Return programming languages as a list"""
        return [lang.strip() for lang in self.programming_languages.split(',') if lang.strip()]
    
    def get_frameworks_list(self):
        """Return frameworks as a list"""
        return [framework.strip() for framework in self.frameworks.split(',') if framework.strip()]
    
    def get_tools_list(self):
        """Return tools as a list"""
        return [tool.strip() for tool in self.tools.split(',') if tool.strip()]
    
    def update_completion_rate(self):
        """Update completion rate based on completed tasks"""
        from services.models import Task
        total_tasks = Task.objects.filter(assigned_to=self.user).count()
        completed_tasks = Task.objects.filter(assigned_to=self.user, status='completed').count()
        
        if total_tasks > 0:
            self.completion_rate = (completed_tasks / total_tasks) * 100
            self.save()
    
    def can_take_new_projects(self):
        """Check if developer can take new projects"""
        if not self.is_accepting_projects or self.availability == 'unavailable':
            return False
        
        # Check current project load
        from services.models import Task
        current_projects = Task.objects.filter(
            assigned_to=self.user,
            status__in=['assigned', 'in_progress']
        ).count()
        
        return current_projects < self.maximum_projects_concurrent
    
    def get_preferred_project_types_display(self):
        """Return preferred project types as readable strings"""
        type_choices = dict(self.PROJECT_TYPE_CHOICES)
        return [type_choices.get(ptype, ptype) for ptype in self.preferred_project_types]
    
    def set_preferred_project_types_from_form(self, selected_types):
        """Set preferred project types from form data"""
        if isinstance(selected_types, list):
            self.preferred_project_types = selected_types
        else:
            self.preferred_project_types = []