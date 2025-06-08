from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserSkill, UserAchievement, UserNotification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'user_type', 'points', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'subscription_tier', 'country']
    search_fields = ['email', 'first_name', 'last_name', 'company']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'bio', 'profile_picture')
        }),
        ('Location', {
            'fields': ('country', 'city', 'address')
        }),
        ('Professional info', {
            'fields': ('user_type', 'company', 'job_title', 'experience_years', 'skill_level', 
                      'linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Account status', {
            'fields': ('points', 'is_verified', 'is_active_developer', 'subscription_tier')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email
    get_full_name.short_description = 'Full Name'
    
    actions = ['verify_users', 'unverify_users', 'activate_developers', 'deactivate_developers']
    
    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {queryset.count()} users.")
    verify_users.short_description = "Verify selected users"
    
    def unverify_users(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {queryset.count()} users.")
    unverify_users.short_description = "Unverify selected users"
    
    def activate_developers(self, request, queryset):
        queryset.filter(user_type='developer').update(is_active_developer=True)
        count = queryset.filter(user_type='developer').count()
        self.message_user(request, f"Successfully activated {count} developers.")
    activate_developers.short_description = "Activate selected developers"
    
    def deactivate_developers(self, request, queryset):
        queryset.filter(user_type='developer').update(is_active_developer=False)
        count = queryset.filter(user_type='developer').count()
        self.message_user(request, f"Successfully deactivated {count} developers.")
    deactivate_developers.short_description = "Deactivate selected developers"

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'category', 'proficiency', 'years_experience', 'is_verified']
    list_filter = ['category', 'proficiency', 'is_verified']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'name']
    ordering = ['-created_at']
    
    actions = ['verify_skills', 'unverify_skills']
    
    def verify_skills(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {queryset.count()} skills.")
    verify_skills.short_description = "Verify selected skills"
    
    def unverify_skills(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {queryset.count()} skills.")
    unverify_skills.short_description = "Unverify selected skills"

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'achievement_type', 'points_awarded', 'earned_date']
    list_filter = ['achievement_type', 'earned_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'title']
    ordering = ['-earned_date']
    date_hierarchy = 'earned_date'

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'title']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"Successfully marked {queryset.count()} notifications as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"Successfully marked {queryset.count()} notifications as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"