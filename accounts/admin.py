# accounts/admin.py - Complete fix for the CountryField issue

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from django.core.exceptions import ValidationError
from .models import User, UserSkill, UserAchievement, UserNotification

class CustomCountryField(forms.ChoiceField):
    """Custom country field that handles the BlankChoiceIterator issue"""
    
    def __init__(self, *args, **kwargs):
        # Import here to avoid circular imports
        from django_countries import countries
        
        # Create choices list manually
        country_choices = [('', '(Select Country)')]
        country_choices.extend(list(countries))
        
        kwargs['choices'] = country_choices
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        """Override validate to handle empty values properly"""
        if value in self.empty_values:
            if self.required:
                raise ValidationError(self.error_messages['required'], code='required')
            else:
                return
        
        # Check if value is in choices
        valid_values = [choice[0] for choice in self.choices]
        if value not in valid_values:
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )

class UserAdminForm(forms.ModelForm):
    """Custom form for User admin to handle CountryField properly"""
    
    # Override the country field with our custom implementation
    country = CustomCountryField(required=False)
    
    class Meta:
        model = User
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set the country field value if instance exists
        if self.instance and self.instance.pk:
            self.fields['country'].initial = str(self.instance.country) if self.instance.country else ''
    
    def clean_country(self):
        """Custom clean method for country field"""
        country = self.cleaned_data.get('country')
        if country == '':
            return None
        return country

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm  # Use our custom form
    
    list_display = ['email', 'get_full_name', 'user_type', 'points', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'subscription_tier']
    search_fields = ['email', 'first_name', 'last_name', 'company']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
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
            'fields': ('email', 'username', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email
    get_full_name.short_description = 'Full Name'
    
    def save_model(self, request, obj, form, change):
        """Override to ensure username is generated if empty"""
        if not obj.username:
            # Generate username if not provided
            if obj.email:
                base_username = obj.email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exclude(pk=obj.pk).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                obj.username = username
            else:
                obj.username = f"user_{obj.pk or 'new'}"
        
        super().save_model(request, obj, form, change)
    
    actions = ['verify_users', 'unverify_users', 'activate_developers', 'deactivate_developers']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {updated} users.")
    verify_users.short_description = "Verify selected users"
    
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {updated} users.")
    unverify_users.short_description = "Unverify selected users"
    
    def activate_developers(self, request, queryset):
        developers = queryset.filter(user_type='developer')
        count = developers.update(is_active_developer=True)
        self.message_user(request, f"Successfully activated {count} developers.")
    activate_developers.short_description = "Activate selected developers"
    
    def deactivate_developers(self, request, queryset):
        developers = queryset.filter(user_type='developer')
        count = developers.update(is_active_developer=False)
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
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {updated} skills.")
    verify_skills.short_description = "Verify selected skills"
    
    def unverify_skills(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {updated} skills.")
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
        updated = queryset.update(is_read=True)
        self.message_user(request, f"Successfully marked {updated} notifications as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"Successfully marked {updated} notifications as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"