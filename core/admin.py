from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count
from .models import (
    SiteSettings, HeroSection, CompanyStatistic, PageContent,
    TeamMember, Announcement, SiteAnalytics, EmailTemplate
)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_tagline', 'site_description', 'site_logo', 'favicon')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address', 'business_hours')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url', 'youtube_url', 'github_url')
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Features & Settings', {
            'fields': ('maintenance_mode', 'allow_registration', 'allow_comments', 'show_testimonials', 'show_stats')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'facebook_pixel_id')
        }),
        ('Email Settings', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_use_tls', 'smtp_username')
        }),
        ('Payment Settings', {
            'fields': ('currency', 'tax_rate')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'show_animated_background', 'show_scroll_indicator']
    search_fields = ['title', 'subtitle']
    list_editable = ['is_active', 'order']
    ordering = ['order']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'subtitle')
        }),
        ('Background', {
            'fields': ('background_image', 'background_video', 'background_color', 'show_animated_background')
        }),
        ('Call-to-Action', {
            'fields': ('primary_button_text', 'primary_button_url', 'secondary_button_text', 'secondary_button_url')
        }),
        ('Display Settings', {
            'fields': ('show_scroll_indicator', 'is_active', 'order')
        }),
    )

@admin.register(CompanyStatistic)
class CompanyStatisticAdmin(admin.ModelAdmin):
    list_display = ['label', 'value', 'stat_type', 'is_active', 'order']
    list_filter = ['stat_type', 'is_active']
    search_fields = ['label', 'value']
    list_editable = ['is_active', 'order']
    ordering = ['order']

@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'page_type', 'is_published', 'show_in_menu', 'order', 'updated_at']
    list_filter = ['page_type', 'is_published', 'show_in_menu']
    search_fields = ['title', 'content']
    list_editable = ['is_published', 'show_in_menu', 'order']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('page_type', 'title', 'slug', 'subtitle')
        }),
        ('Content', {
            'fields': ('content', 'featured_image')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description')
        }),
        ('Display Settings', {
            'fields': ('show_in_menu', 'is_published', 'order')
        }),
    )

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'role', 'is_featured', 'is_active', 'joined_date']
    list_filter = ['role', 'is_featured', 'is_active', 'joined_date']
    search_fields = ['name', 'title', 'bio']
    list_editable = ['is_featured', 'is_active']
    date_hierarchy = 'joined_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'role', 'title', 'bio', 'photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'twitter_url', 'github_url', 'portfolio_url')
        }),
        ('Professional Details', {
            'fields': ('specializations', 'experience_years', 'joined_date')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related()

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'is_current', 'is_active', 'start_date', 'end_date']
    list_filter = ['announcement_type', 'is_active', 'show_on_homepage', 'show_on_dashboard', 'start_date']
    search_fields = ['title', 'message']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'message', 'announcement_type')
        }),
        ('Display Settings', {
            'fields': ('show_on_homepage', 'show_on_dashboard', 'show_to_all_users', 'show_to_logged_in_only')
        }),
        ('Targeting', {
            'fields': ('target_user_types',)
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Interaction', {
            'fields': ('is_dismissible', 'action_url', 'action_text')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def is_current(self, obj):
        return obj.is_current
    is_current.boolean = True
    is_current.short_description = 'Currently Active'
    
    actions = ['activate_announcements', 'deactivate_announcements']
    
    def activate_announcements(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} announcements.")
    activate_announcements.short_description = "Activate selected announcements"
    
    def deactivate_announcements(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} announcements.")
    deactivate_announcements.short_description = "Deactivate selected announcements"

@admin.register(SiteAnalytics)
class SiteAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_page_views', 'unique_visitors', 'new_registrations',
        'contact_form_submissions', 'newsletter_signups'
    ]
    list_filter = ['date']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Page Views', {
            'fields': ('homepage_views', 'services_views', 'blog_views', 'dashboard_views', 'total_page_views')
        }),
        ('User Interactions', {
            'fields': ('unique_visitors', 'new_registrations', 'contact_form_submissions', 'newsletter_signups')
        }),
        ('Engagement Metrics', {
            'fields': ('average_session_duration', 'bounce_rate')
        }),
        ('Device Breakdown', {
            'fields': ('desktop_users', 'mobile_users', 'tablet_users')
        }),
        ('Traffic Sources', {
            'fields': ('organic_traffic', 'direct_traffic', 'social_traffic', 'referral_traffic')
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject', 'html_content']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'subject')
        }),
        ('Content', {
            'fields': ('html_content', 'text_content')
        }),
        ('Variables', {
            'fields': ('available_variables',),
            'description': 'Available template variables in JSON format'
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.template_type:
            return ['template_type']
        return []

# Custom admin site branding
admin.site.site_header = "Debsploit Solutions Administration"
admin.site.site_title = "Debsploit Admin"
admin.site.index_title = "Welcome to Debsploit Solutions Admin Panel"

# Add custom CSS and JS to admin
class DebsploitAdminSite(admin.AdminSite):
    site_header = "Debsploit Solutions Administration"
    site_title = "Debsploit Admin"
    index_title = "Dashboard"
    
    def each_context(self, request):
        context = super().each_context(request)
        
        # Add custom context for admin dashboard
        if request.user.is_authenticated and request.user.is_staff:
            from django.utils import timezone
            from accounts.models import User
            from services.models import Service, Task
            from blog.models import BlogPost, ContactMessage
            
            today = timezone.now().date()
            
            # Quick stats for admin dashboard
            context.update({
                'quick_stats': {
                    'total_users': User.objects.count(),
                    'new_users_today': User.objects.filter(date_joined__date=today).count(),
                    'total_services': Service.objects.filter(is_active=True).count(),
                    'open_tasks': Task.objects.filter(status='open').count(),
                    'pending_contact_messages': ContactMessage.objects.filter(status='new').count(),
                    'published_blog_posts': BlogPost.objects.filter(status='published').count(),
                }
            })
        
        return context