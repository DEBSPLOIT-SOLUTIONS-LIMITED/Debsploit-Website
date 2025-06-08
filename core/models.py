from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField

User = get_user_model()

class SiteSettings(models.Model):
    """Global site settings and configuration"""
    # Site Information
    site_name = models.CharField(max_length=200, default="Debsploit Solutions")
    site_tagline = models.CharField(max_length=300, default="Empowering Communities with Digital Skills")
    site_description = RichTextUploadingField(default="Transform your future with cutting-edge technology training and professional tech services")
    site_logo = models.ImageField(upload_to='site_media/', blank=True)
    favicon = models.ImageField(upload_to='site_media/', blank=True)
    
    # Contact Information
    contact_email = models.EmailField(default="info@debsploit.com")
    contact_phone = models.CharField(max_length=20, default="+254 468 38304")
    contact_address = models.TextField(default="Nairobi, Kenya")
    
    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    
    # Business Hours
    business_hours = models.TextField(default="Monday - Friday: 8:00 AM - 6:00 PM\nSaturday: 9:00 AM - 4:00 PM\nSunday: Closed")
    
    # SEO Settings
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Feature Flags
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    show_testimonials = models.BooleanField(default=True)
    show_stats = models.BooleanField(default=True)
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    
    # Email Settings
    smtp_host = models.CharField(max_length=200, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_username = models.CharField(max_length=200, blank=True)
    
    # Payment Settings
    currency = models.CharField(max_length=3, default='KES')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('Only one SiteSettings instance is allowed.')
        super().save(*args, **kwargs)

class HeroSection(models.Model):
    """Hero section content for homepage"""
    title = models.CharField(max_length=200, default="Empowering Communities with Digital Skills")
    subtitle = models.TextField(default="Transform your future with cutting-edge technology training and professional tech services")
    background_image = models.ImageField(upload_to='hero_images/', blank=True)
    background_video = models.FileField(upload_to='hero_videos/', blank=True)
    background_color = models.CharField(max_length=7, default="#667eea")
    
    # Call-to-action buttons
    primary_button_text = models.CharField(max_length=50, default="Explore Services")
    primary_button_url = models.CharField(max_length=200, default="#services")
    secondary_button_text = models.CharField(max_length=50, default="Get Quote")
    secondary_button_url = models.CharField(max_length=200, default="#contact")
    
    # Display settings
    show_animated_background = models.BooleanField(default=True)
    show_scroll_indicator = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Hero: {self.title}"

class CompanyStatistic(models.Model):
    """Company statistics displayed on homepage"""
    STAT_TYPES = (
        ('students_trained', 'Students Trained'),
        ('job_placement_rate', 'Job Placement Rate'),
        ('corporate_clients', 'Corporate Clients'),
        ('projects_completed', 'Projects Completed'),
        ('years_experience', 'Years Experience'),
        ('success_rate', 'Success Rate'),
        ('custom', 'Custom'),
    )
    
    stat_type = models.CharField(max_length=20, choices=STAT_TYPES)
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=20, help_text="e.g., 500+, 95%, $1M+")
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default="#0066FF")
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.label}: {self.value}"

class PageContent(models.Model):
    """Dynamic page content for different sections"""
    PAGE_CHOICES = (
        ('about', 'About Us'),
        ('services', 'Services'),
        ('contact', 'Contact'),
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms of Service'),
        ('custom', 'Custom Page'),
    )
    
    page_type = models.CharField(max_length=20, choices=PAGE_CHOICES)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    content = RichTextUploadingField()
    featured_image = models.ImageField(upload_to='page_images/', blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Display settings
    show_in_menu = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title

class TeamMember(models.Model):
    """Company team members"""
    ROLE_CHOICES = (
        ('founder', 'Founder'),
        ('ceo', 'CEO'),
        ('cto', 'CTO'),
        ('instructor', 'Lead Instructor'),
        ('developer', 'Senior Developer'),
        ('designer', 'Design Lead'),
        ('marketing', 'Marketing Manager'),
        ('support', 'Support Specialist'),
        ('consultant', 'Consultant'),
    )
    
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    title = models.CharField(max_length=200)
    bio = models.TextField()
    photo = models.ImageField(upload_to='team_photos/')
    
    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Social Links
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Skills
    specializations = models.TextField(help_text="Comma-separated list of specializations")
    experience_years = models.PositiveIntegerField(default=0)
    
    # Display settings
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    joined_date = models.DateField(default=timezone.now)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.title}"

class Announcement(models.Model):
    """Site-wide announcements"""
    ANNOUNCEMENT_TYPES = (
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('danger', 'Urgent'),
        ('promotion', 'Promotion'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='info')
    
    # Display settings
    show_on_homepage = models.BooleanField(default=True)
    show_on_dashboard = models.BooleanField(default=True)
    show_to_all_users = models.BooleanField(default=True)
    show_to_logged_in_only = models.BooleanField(default=False)
    
    # Targeting
    target_user_types = models.CharField(max_length=100, blank=True, 
                                       help_text="Comma-separated: student,developer,instructor,admin")
    
    # Timing
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Interaction
    is_dismissible = models.BooleanField(default=True)
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def is_current(self):
        now = timezone.now()
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now

class SiteAnalytics(models.Model):
    """Daily site analytics"""
    date = models.DateField(unique=True, default=timezone.now)
    
    # Page views
    homepage_views = models.PositiveIntegerField(default=0)
    services_views = models.PositiveIntegerField(default=0)
    blog_views = models.PositiveIntegerField(default=0)
    dashboard_views = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    
    # User interactions
    unique_visitors = models.PositiveIntegerField(default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    contact_form_submissions = models.PositiveIntegerField(default=0)
    newsletter_signups = models.PositiveIntegerField(default=0)
    
    # Engagement
    average_session_duration = models.DurationField(null=True, blank=True)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Device breakdown
    desktop_users = models.PositiveIntegerField(default=0)
    mobile_users = models.PositiveIntegerField(default=0)
    tablet_users = models.PositiveIntegerField(default=0)
    
    # Traffic sources
    organic_traffic = models.PositiveIntegerField(default=0)
    direct_traffic = models.PositiveIntegerField(default=0)
    social_traffic = models.PositiveIntegerField(default=0)
    referral_traffic = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Site Analytics"
    
    def __str__(self):
        return f"Analytics for {self.date}"

class EmailTemplate(models.Model):
    """Email templates for automated emails"""
    TEMPLATE_TYPES = (
        ('welcome', 'Welcome Email'),
        ('enrollment_confirmation', 'Enrollment Confirmation'),
        ('task_assignment', 'Task Assignment'),
        ('task_completion', 'Task Completion'),
        ('password_reset', 'Password Reset'),
        ('newsletter', 'Newsletter'),
        ('promotion', 'Promotional Email'),
        ('reminder', 'Reminder Email'),
    )
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    html_content = RichTextUploadingField()
    text_content = models.TextField(blank=True)
    
    # Variables that can be used in template
    available_variables = models.TextField(
        blank=True,
        help_text="JSON format of available variables like {user_name}, {course_name}, etc."
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['template_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"