from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField
from PIL import Image

class User(AbstractUser):
    USER_TYPES = (
        ('student', 'Student'),
        ('developer', 'Developer'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    )
    
    SKILL_LEVELS = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    phone = PhoneNumberField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg')
    date_of_birth = models.DateField(null=True, blank=True)
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    # Professional Info
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='beginner')
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Account Info
    points = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_active_developer = models.BooleanField(default=False)
    subscription_tier = models.CharField(max_length=20, default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_absolute_url(self):
        return reverse('dashboard:profile', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize profile picture
        if self.profile_picture:
            img = Image.open(self.profile_picture.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_picture.path)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_developer(self):
        return self.user_type == 'developer'
    
    @property
    def is_instructor(self):
        return self.user_type == 'instructor'
    
    def add_points(self, points):
        self.points += points
        self.save()
    
    def deduct_points(self, points):
        if self.points >= points:
            self.points -= points
            self.save()
            return True
        return False

class UserSkill(models.Model):
    SKILL_CATEGORIES = (
        ('programming', 'Programming'),
        ('design', 'Design'),
        ('cybersecurity', 'Cybersecurity'),
        ('networking', 'Networking'),
        ('ai_ml', 'AI/ML'),
        ('marketing', 'Digital Marketing'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES)
    proficiency = models.CharField(max_length=20, choices=User.SKILL_LEVELS)
    years_experience = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"

class UserAchievement(models.Model):
    ACHIEVEMENT_TYPES = (
        ('course_completion', 'Course Completion'),
        ('project_completion', 'Project Completion'),
        ('certification', 'Certification'),
        ('points_milestone', 'Points Milestone'),
        ('special_recognition', 'Special Recognition'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    points_awarded = models.PositiveIntegerField(default=0)
    badge_icon = models.CharField(max_length=50, default='fas fa-trophy')
    earned_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"

class UserNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('points_earned', 'Points Earned'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('course_enrolled', 'Course Enrolled'),
        ('system_update', 'System Update'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"