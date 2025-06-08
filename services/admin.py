from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from django.contrib import messages
from .models import (
    ServiceCategory, Service, Course, Enrollment, Task, TaskApplication,
    TaskSubmission, ServiceReview, CompanyInfo
)
from accounts.models import UserSkill

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_count', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'name']
    prepopulated_fields = {'slug': ('name',)}
    
    def service_count(self, obj):
        count = obj.services.count()
        url = reverse('admin:services_service_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} services</a>', url, count)
    service_count.short_description = 'Services'
    
    actions = ['activate_categories', 'deactivate_categories']
    
    def activate_categories(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} categories.")
    activate_categories.short_description = "Activate selected categories"
    
    def deactivate_categories(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} categories.")
    deactivate_categories.short_description = "Deactivate selected categories"

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'service_type', 'difficulty_level', 'price',
        'discount_price', 'enrollment_count', 'average_rating', 'is_featured',
        'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'service_type', 'difficulty_level', 'is_active',
        'is_featured', 'created_at'
    ]
    search_fields = ['title', 'description', 'detailed_description']
    list_editable = ['is_featured', 'is_active']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['total_enrollments', 'average_rating', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'description', 'detailed_description')
        }),
        ('Service Details', {
            'fields': ('service_type', 'difficulty_level', 'duration_weeks', 'max_participants')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'currency')
        }),
        ('Media', {
            'fields': ('featured_image', 'video_url')
        }),
        ('Requirements', {
            'fields': ('prerequisites', 'required_tools')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('total_enrollments', 'average_rating', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def enrollment_count(self, obj):
        count = obj.course.enrollments.count() if hasattr(obj, 'course') else 0
        if count > 0:
            url = reverse('admin:services_enrollment_changelist') + f'?course__service__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return count
    enrollment_count.short_description = 'Enrollments'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category').annotate(
            enrollment_count=Count('course__enrollments')
        )
    
    actions = ['feature_services', 'unfeature_services', 'activate_services', 'deactivate_services']
    
    def feature_services(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"Successfully featured {queryset.count()} services.")
    feature_services.short_description = "Feature selected services"
    
    def unfeature_services(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"Successfully unfeatured {queryset.count()} services.")
    unfeature_services.short_description = "Unfeature selected services"
    
    def activate_services(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} services.")
    activate_services.short_description = "Activate selected services"
    
    def deactivate_services(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} services.")
    deactivate_services.short_description = "Deactivate selected services"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'service', 'instructor', 'start_date', 'end_date', 'current_enrollment',
        'max_capacity', 'enrollment_percentage', 'is_enrollment_open'
    ]
    list_filter = ['is_enrollment_open', 'start_date', 'service__category']
    search_fields = ['service__title', 'instructor__first_name', 'instructor__last_name']
    list_editable = ['is_enrollment_open']
    date_hierarchy = 'start_date'
    raw_id_fields = ['service', 'instructor']
    
    fieldsets = (
        ('Course Details', {
            'fields': ('service', 'instructor', 'start_date', 'end_date')
        }),
        ('Schedule & Location', {
            'fields': ('schedule', 'location', 'meeting_link')
        }),
        ('Materials', {
            'fields': ('syllabus', 'resources')
        }),
        ('Enrollment', {
            'fields': ('is_enrollment_open', 'current_enrollment')
        }),
    )
    
    readonly_fields = ['current_enrollment']
    
    def max_capacity(self, obj):
        return obj.service.max_participants
    max_capacity.short_description = 'Max Capacity'
    
    def enrollment_percentage(self, obj):
        percentage = obj.enrollment_percentage
        color = 'green' if percentage < 80 else 'orange' if percentage < 100 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentage
        )
    enrollment_percentage.short_description = 'Enrollment %'

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ['enrolled_date', 'progress_percentage', 'points_earned']
    fields = ['user', 'status', 'progress_percentage', 'payment_status', 'amount_paid', 'enrolled_date']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'course_title', 'status', 'progress_percentage',
        'payment_status', 'enrolled_date', 'completion_date'
    ]
    list_filter = ['status', 'payment_status', 'enrolled_date', 'course__service__category']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'course__service__title']
    list_editable = ['status', 'payment_status']
    date_hierarchy = 'enrolled_date'
    raw_id_fields = ['user', 'course']
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('user', 'course', 'status', 'enrolled_date')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'completion_date', 'final_grade', 'points_earned')
        }),
        ('Payment', {
            'fields': ('payment_status', 'amount_paid')
        }),
    )
    
    readonly_fields = ['enrolled_date']
    
    def course_title(self, obj):
        return obj.course.service.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__service__title'
    
    actions = ['mark_completed', 'mark_active', 'send_completion_certificates']
    
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', completion_date=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} enrollments as completed.")
    mark_completed.short_description = "Mark selected enrollments as completed"
    
    def mark_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"Marked {queryset.count()} enrollments as active.")
    mark_active.short_description = "Mark selected enrollments as active"

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'task_type', 'priority', 'status', 'assigned_to',
        'budget', 'due_date', 'is_overdue', 'created_at'
    ]
    list_filter = ['task_type', 'priority', 'status', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'requirements']
    list_editable = ['priority', 'status']
    date_hierarchy = 'created_at'
    raw_id_fields = ['assigned_to', 'assigned_by']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_type', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_by', 'assigned_date')
        }),
        ('Timeline', {
            'fields': ('estimated_hours', 'actual_hours', 'due_date', 'completed_date')
        }),
        ('Requirements', {
            'fields': ('required_skills', 'requirements', 'deliverables', 'attachment')
        }),
        ('Compensation', {
            'fields': ('budget', 'points_reward')
        }),
    )
    
    readonly_fields = ['assigned_date', 'completed_date', 'created_at', 'updated_at']
    
    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue.short_description = 'Overdue'
    is_overdue.boolean = True
    
    actions = ['mark_in_progress', 'mark_completed', 'mark_cancelled']
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
        self.message_user(request, f"Marked {queryset.count()} tasks as in progress.")
    mark_in_progress.short_description = "Mark as in progress"
    
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', completed_date=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} tasks as completed.")
    mark_completed.short_description = "Mark as completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"Cancelled {queryset.count()} tasks.")
    mark_cancelled.short_description = "Cancel selected tasks"

@admin.register(TaskApplication)
class TaskApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'applicant', 'task_title', 'status', 'proposed_budget',
        'applied_date', 'reviewed_date', 'reviewed_by'
    ]
    list_filter = ['status', 'applied_date', 'reviewed_date']
    search_fields = ['applicant__email', 'task__title', 'cover_letter']
    raw_id_fields = ['task', 'applicant', 'reviewed_by']
    date_hierarchy = 'applied_date'
    
    fieldsets = (
        ('Application Details', {
            'fields': ('task', 'applicant', 'status', 'applied_date')
        }),
        ('Proposal', {
            'fields': ('cover_letter', 'proposed_timeline', 'proposed_budget')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_date')
        }),
    )
    
    readonly_fields = ['applied_date', 'reviewed_date']
    
    def task_title(self, obj):
        return obj.task.title
    task_title.short_description = 'Task'
    task_title.admin_order_field = 'task__title'
    
    actions = ['accept_applications', 'reject_applications']
    
    def accept_applications(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='accepted',
            reviewed_by=request.user,
            reviewed_date=timezone.now()
        )
        self.message_user(request, f"Accepted {queryset.count()} applications.")
    accept_applications.short_description = "Accept selected applications"
    
    def reject_applications(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_date=timezone.now()
        )
        self.message_user(request, f"Rejected {queryset.count()} applications.")
    reject_applications.short_description = "Reject selected applications"

@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'task_title', 'submitted_by', 'status', 'is_approved', 'submitted_date',
        'reviewed_by', 'reviewed_date'
    ]
    list_filter = ['status', 'is_approved', 'submitted_date', 'reviewed_date']
    search_fields = ['task__title', 'submitted_by__email', 'description']
    raw_id_fields = ['task', 'submitted_by', 'reviewed_by']
    date_hierarchy = 'submitted_date'
    
    fieldsets = (
        ('Submission Details', {
            'fields': ('task', 'submitted_by', 'status', 'submitted_date')
        }),
        ('Content', {
            'fields': ('description', 'files', 'github_link', 'demo_link')
        }),
        ('Review', {
            'fields': ('is_approved', 'reviewer_feedback', 'reviewed_by', 'reviewed_date')
        }),
    )
    
    readonly_fields = ['submitted_date', 'reviewed_date']
    
    def task_title(self, obj):
        return obj.task.title
    task_title.short_description = 'Task'
    task_title.admin_order_field = 'task__title'
    
    actions = ['approve_submissions', 'reject_submissions', 'mark_under_review']
    
    def approve_submissions(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='approved',
            is_approved=True,
            reviewed_by=request.user,
            reviewed_date=timezone.now()
        )
        self.message_user(request, f"Approved {queryset.count()} submissions.")
    approve_submissions.short_description = "Approve selected submissions"
    
    def reject_submissions(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='rejected',
            is_approved=False,
            reviewed_by=request.user,
            reviewed_date=timezone.now()
        )
        self.message_user(request, f"Rejected {queryset.count()} submissions.")
    reject_submissions.short_description = "Reject selected submissions"
    
    def mark_under_review(self, request, queryset):
        queryset.update(status='under_review')
        self.message_user(request, f"Marked {queryset.count()} submissions as under review.")
    mark_under_review.short_description = "Mark as under review"

@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = [
        'service', 'user', 'rating', 'title', 'is_verified', 'created_at'
    ]
    list_filter = ['rating', 'is_verified', 'created_at', 'service__category']
    search_fields = ['service__title', 'user__email', 'user__first_name', 'user__last_name', 'title', 'comment']
    list_editable = ['is_verified']
    date_hierarchy = 'created_at'
    raw_id_fields = ['service', 'user']
    
    fieldsets = (
        ('Review Details', {
            'fields': ('service', 'user', 'rating', 'title', 'comment')
        }),
        ('Moderation', {
            'fields': ('is_verified', 'created_at')
        }),
    )
    
    readonly_fields = ['created_at']
    
    actions = ['verify_reviews', 'unverify_reviews']
    
    def verify_reviews(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Verified {queryset.count()} reviews.")
    verify_reviews.short_description = "Verify selected reviews"
    
    def unverify_reviews(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f"Unverified {queryset.count()} reviews.")
    unverify_reviews.short_description = "Unverify selected reviews"

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'city', 'country', 'updated_at']
    search_fields = ['name', 'email', 'city', 'country']
    
    fieldsets = (
        ('Company Details', {
            'fields': ('name', 'tagline', 'description')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'country', 'postal_code')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url', 'youtube_url')
        }),
        ('Business Information', {
            'fields': ('founded_year', 'employees_count', 'students_trained', 'projects_completed')
        }),
        ('Settings', {
            'fields': ('is_enrollment_open', 'maintenance_mode')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one company info record
        return not CompanyInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

# Custom admin site configuration
admin.site.site_header = "Debsploit Solutions Admin"
admin.site.site_title = "Debsploit Admin Portal"
admin.site.index_title = "Welcome to Debsploit Solutions Administration"