from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import UserNotification, UserAchievement, UserSkill
from dashboard.models import UserProgress, DeveloperProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile_data(sender, instance, created, **kwargs):
    """Create related profile data when user is created"""
    if created:
        # Create user progress
        UserProgress.objects.get_or_create(user=instance)
        
        # Create developer profile if user is a developer
        if instance.user_type == 'developer':
            DeveloperProfile.objects.get_or_create(user=instance)
        
        # Send welcome notification
        UserNotification.objects.create(
            user=instance,
            title='Welcome to Debsploit Solutions!',
            message=f'Welcome {instance.get_full_name() or instance.username}! Start your learning journey today.',
            notification_type='system_update'
        )
        
        # Award welcome achievement
        UserAchievement.objects.create(
            user=instance,
            title='Welcome Aboard!',
            description='Joined the Debsploit Solutions community',
            achievement_type='special_recognition',
            points_awarded=10,
            badge_icon='fas fa-hand-wave'
        )
        
        # Add welcome points
        instance.points = 10
        instance.save(update_fields=['points'])
        
        # Send welcome email
        send_welcome_email(instance)

@receiver(pre_save, sender=User)
def check_user_changes(sender, instance, **kwargs):
    """Check for important user changes"""
    if instance.pk:  # User already exists
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Check if user was verified
            if not old_instance.is_verified and instance.is_verified:
                # Award verification achievement
                UserAchievement.objects.create(
                    user=instance,
                    title='Verified User',
                    description='Account has been verified',
                    achievement_type='special_recognition',
                    points_awarded=50,
                    badge_icon='fas fa-check-circle'
                )
                
                # Send verification notification
                UserNotification.objects.create(
                    user=instance,
                    title='Account Verified!',
                    message='Your account has been verified. You now have access to all features.',
                    notification_type='system_update'
                )
                
                # Add verification points
                instance.points += 50
            
            # Check if user type changed to developer
            if old_instance.user_type != 'developer' and instance.user_type == 'developer':
                # Create developer profile
                DeveloperProfile.objects.get_or_create(user=instance)
                
                # Send notification
                UserNotification.objects.create(
                    user=instance,
                    title='Developer Status Activated',
                    message='You are now a developer! Start applying for tasks and building your portfolio.',
                    notification_type='system_update'
                )
                
        except User.DoesNotExist:
            pass

@receiver(post_save, sender=UserSkill)
def skill_added_notification(sender, instance, created, **kwargs):
    """Notify user when a new skill is added"""
    if created:
        UserNotification.objects.create(
            user=instance.user,
            title='New Skill Added',
            message=f'You added {instance.name} to your skills with {instance.proficiency} proficiency.',
            notification_type='achievement_unlocked'
        )
        
        # Award points for adding skills
        instance.user.add_points(5)
        
        # Check for skill milestone achievements
        skill_count = UserSkill.objects.filter(user=instance.user).count()
        
        if skill_count == 5:
            UserAchievement.objects.create(
                user=instance.user,
                title='Skill Collector',
                description='Added 5 skills to your profile',
                achievement_type='points_milestone',
                points_awarded=25,
                badge_icon='fas fa-collection'
            )
        elif skill_count == 10:
            UserAchievement.objects.create(
                user=instance.user,
                title='Skill Master',
                description='Added 10 skills to your profile',
                achievement_type='points_milestone',
                points_awarded=50,
                badge_icon='fas fa-crown'
            )

@receiver(post_save, sender=UserAchievement)
def achievement_earned_notification(sender, instance, created, **kwargs):
    """Send notification when user earns an achievement"""
    if created:
        UserNotification.objects.create(
            user=instance.user,
            title='Achievement Unlocked!',
            message=f'You earned the "{instance.title}" achievement!',
            notification_type='achievement_unlocked'
        )
        
        # Add achievement points to user
        if instance.points_awarded > 0:
            instance.user.add_points(instance.points_awarded)

def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        subject = 'Welcome to Debsploit Solutions!'
        
        html_message = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_name': 'Debsploit Solutions',
            'login_url': f"{settings.SITE_URL}/accounts/login/",
            'dashboard_url': f"{settings.SITE_URL}/dashboard/",
        })
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send welcome email to {user.email}: {e}")

def send_verification_email(user):
    """Send verification success email"""
    try:
        subject = 'Account Verified - Debsploit Solutions'
        
        html_message = render_to_string('emails/verification_email.html', {
            'user': user,
            'site_name': 'Debsploit Solutions',
            'dashboard_url': f"{settings.SITE_URL}/dashboard/",
        })
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send verification email to {user.email}: {e}")

# Achievement triggers for various milestones
def check_points_milestones(user):
    """Check and award points milestone achievements"""
    points = user.points
    
    milestones = [
        (100, 'First Century', 'Earned your first 100 points'),
        (500, 'Point Collector', 'Accumulated 500 points'),
        (1000, 'Thousand Club', 'Reached 1000 points'),
        (2500, 'Point Master', 'Achieved 2500 points'),
        (5000, 'Point Legend', 'Accumulated 5000 points'),
    ]
    
    for threshold, title, description in milestones:
        if points >= threshold:
            # Check if achievement already exists
            if not UserAchievement.objects.filter(
                user=user,
                title=title
            ).exists():
                UserAchievement.objects.create(
                    user=user,
                    title=title,
                    description=description,
                    achievement_type='points_milestone',
                    points_awarded=threshold // 10,  # Bonus points
                    badge_icon='fas fa-trophy'
                )

# Connect points milestone checker
@receiver(post_save, sender=User)
def check_user_milestones(sender, instance, **kwargs):
    """Check for various user milestones"""
    if instance.pk:  # Only for existing users
        check_points_milestones(instance)