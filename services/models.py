from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from ckeditor_uploader.fields import RichTextUploadingField
from mptt.models import MPTTModel, TreeForeignKey

User = get_user_model()

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default="#0070f2", help_text="Hex color code")
    
    # Add parent field first without MPTT
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Meta fields
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, help_text="SEO title (leave blank to use name)")
    meta_description = models.TextField(max_length=300, blank=True, help_text="SEO description")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Service Categories"
    
    def __str__(self):
        return self.get_full_name()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Ensure slug uniqueness
            while ServiceCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('services:category_detail', kwargs={'slug': self.slug})
    
    def get_full_name(self):
        """Return the full category path like 'Technology > Web Development > Frontend'"""
        if self.parent:
            return f"{self.parent.get_full_name()} > {self.name}"
        return self.name
    
    def get_breadcrumb_path(self):
        """Return list of categories from root to current for breadcrumbs"""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path
    
    def get_all_services(self):
        """Get all services in this category and its subcategories"""
        def get_descendants(category):
            descendants = [category]
            for child in category.children.all():
                descendants.extend(get_descendants(child))
            return descendants
        
        descendant_categories = get_descendants(self)
        return Service.objects.filter(category__in=descendant_categories, is_active=True)
    
    def get_direct_services_count(self):
        """Get count of services directly in this category (not subcategories)"""
        return self.services.filter(is_active=True).count()
    
    def get_total_services_count(self):
        """Get total count of services in this category and all subcategories"""
        return self.get_all_services().count()
    
    def get_subcategories(self):
        """Get direct subcategories only"""
        return self.children.filter(is_active=True).order_by('order', 'name')
    
    def has_subcategories(self):
        """Check if this category has any subcategories"""
        return self.get_subcategories().exists()
    
    def is_root_category(self):
        """Check if this is a root category (no parent)"""
        return self.parent is None
    
    def get_root_category(self):
        """Get the root category of this category"""
        current = self
        while current.parent:
            current = current.parent
        return current
    
    def get_siblings(self):
        """Get sibling categories (same parent level)"""
        if self.parent:
            return self.parent.children.filter(is_active=True).exclude(pk=self.pk)
        else:
            return ServiceCategory.objects.filter(parent=None, is_active=True).exclude(pk=self.pk)
    
    def get_level(self):
        """Get the depth level of this category"""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level

class Service(models.Model):
    DIFFICULTY_LEVELS = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )
    
    SERVICE_TYPES = (
        ('training', 'Training Program'),
        ('consultation', 'Consultation'),
        ('installation', 'Installation'),
        ('maintenance', 'Maintenance'),
        ('development', 'Development'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    description = models.TextField()
    detailed_description = RichTextUploadingField()
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='training')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='beginner')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='KSH')
    
    # Duration and capacity
    duration_weeks = models.PositiveIntegerField(help_text="Duration in weeks")
    max_participants = models.PositiveIntegerField(default=50)
    
    # Media
    featured_image = models.ImageField(upload_to='service_images/', blank=True)
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")
    
    # Requirements
    prerequisites = models.TextField(blank=True, help_text="What students need to know before starting")
    required_tools = models.TextField(blank=True, help_text="Software/tools required")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('services:service_detail', kwargs={'slug': self.slug})
    
    @property
    def effective_price(self):
        """Return the effective price (discount price if available, otherwise regular price)."""
        return self.discount_price if self.has_discount else self.price
    
    @property
    def discount_percentage(self):
        """Calculate the discount percentage."""
        if self.discount_price and self.price > self.discount_price:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    @property
    def discount_amount(self):
        """Calculate the discount amount if there's a discount price."""
        if self.discount_price and self.price > self.discount_price:
            return self.price - self.discount_price
        return 0
    
    @property
    def has_discount(self):
        """Check if service has a discount."""
        return self.discount_price and self.price > self.discount_price
    
    @property
    def original_price(self):
        """Return the original price for template compatibility."""
        if self.has_discount:
            return self.price
        return None
    
    @property
    def duration(self):
        """Return formatted duration string."""
        if not self.duration_weeks:
            return "Self-paced"
        
        weeks = self.duration_weeks
        if weeks == 1:
            return "1 week"
        elif weeks < 4:
            return f"{weeks} weeks"
        elif weeks < 52:
            months = round(weeks / 4.33)
            return f"{months} month{'s' if months != 1 else ''}"
        else:
            years = round(weeks / 52)
            return f"{years} year{'s' if years != 1 else ''}"
class Course(models.Model):
    service = models.OneToOneField(Service, on_delete=models.CASCADE, related_name='course')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    start_date = models.DateField()
    end_date = models.DateField()
    schedule = models.TextField(help_text="Class schedule and timing")
    location = models.CharField(max_length=200, blank=True, help_text="Physical or online location")
    meeting_link = models.URLField(blank=True, help_text="Zoom/Meet link for online classes")
    
    # Course materials
    syllabus = models.FileField(upload_to='course_materials/', blank=True)
    resources = RichTextUploadingField(blank=True, help_text="Links to additional resources")
    
    # Status
    is_enrollment_open = models.BooleanField(default=True)
    current_enrollment = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.service.title} - {self.start_date}"
    
    @property
    def is_full(self):
        return self.current_enrollment >= self.service.max_participants
    
    @property
    def enrollment_percentage(self):
        if self.service.max_participants > 0:
            return (self.current_enrollment / self.service.max_participants) * 100
        return 0

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    enrolled_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.PositiveIntegerField(default=0)
    final_grade = models.CharField(max_length=2, blank=True)
    points_earned = models.PositiveIntegerField(default=0)
    
    # Payment info
    payment_status = models.CharField(max_length=20, default='pending')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.course.service.title}"

class Task(models.Model):
    TASK_TYPES = (
        ('development', 'Development'),
        ('design', 'Design'),
        ('testing', 'Testing'),
        ('documentation', 'Documentation'),
        ('consultation', 'Consultation'),
        ('training', 'Training'),
        ('maintenance', 'Maintenance'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    description = RichTextUploadingField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_date = models.DateTimeField(null=True, blank=True)
    
    # Timing
    estimated_hours = models.PositiveIntegerField(help_text="Estimated hours to complete")
    actual_hours = models.PositiveIntegerField(default=0)
    due_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Requirements (Fixed - removed the problematic ManyToMany field)
    # Instead of ManyToMany to UserSkill, use a simple text field
    required_skills = models.TextField(blank=True, help_text="Comma-separated list of required skills")
    requirements = models.TextField(blank=True)
    deliverables = models.TextField(blank=True)
    
    # Payment
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    points_reward = models.PositiveIntegerField(default=0)
    
    # Files
    attachment = models.FileField(upload_to='task_attachments/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('dashboard:task_detail', kwargs={'pk': self.pk})
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now() and self.status not in ['completed', 'cancelled']
    
    def get_required_skills_list(self):
        """Return required skills as a list"""
        return [skill.strip() for skill in self.required_skills.split(',') if skill.strip()]

class TaskApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_applications')
    cover_letter = models.TextField()
    proposed_timeline = models.TextField()
    proposed_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reviewed_applications')
    
    class Meta:
        unique_together = ['task', 'applicant']
        ordering = ['-applied_date']
    
    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.task.title}"

class TaskSubmission(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('needs_revision', 'Needs Revision'),
        ('rejected', 'Rejected'),
    )
    
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='submission')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = RichTextUploadingField()
    files = models.FileField(upload_to='task_submissions/', blank=True)
    github_link = models.URLField(blank=True)
    demo_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_date = models.DateTimeField(auto_now_add=True)
    
    # Review
    is_approved = models.BooleanField(default=False)
    reviewer_feedback = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reviewed_submissions')
    reviewed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Submission for {self.task.title}"

class ServiceReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['service', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.service.title} ({self.rating}/5)"

class CompanyInfo(models.Model):
    name = models.CharField(max_length=200, default="Debsploit Solutions")
    tagline = models.CharField(max_length=300)
    description = RichTextUploadingField()
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # Business Info
    founded_year = models.PositiveIntegerField(default=2020)
    employees_count = models.PositiveIntegerField(default=50)
    students_trained = models.PositiveIntegerField(default=500)
    projects_completed = models.PositiveIntegerField(default=100)
    
    # Settings
    is_enrollment_open = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Information"
        verbose_name_plural = "Company Information"
    
    def __str__(self):
        return self.name