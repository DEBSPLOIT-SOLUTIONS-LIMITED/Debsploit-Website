from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from .models import BlogPost, BlogComment, Newsletter
from accounts.models import UserNotification, UserAchievement
from dashboard.models import UserActivity

@receiver(pre_save, sender=BlogPost)
def blog_post_pre_save(sender, instance, **kwargs):
    """Handle blog post pre-save operations"""
    # Auto-generate slug if not provided
    if not instance.slug:
        instance.slug = slugify(instance.title)
        
        # Ensure slug is unique
        original_slug = instance.slug
        counter = 1
        while BlogPost.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1
    
    # Auto-calculate reading time if content exists
    if instance.content:
        word_count = len(instance.content.split())
        instance.reading_time = max(1, word_count // 200)  # 200 words per minute
    
    # Set published date when status changes to published
    if instance.status == 'published' and not instance.published_date:
        instance.published_date = timezone.now()

@receiver(post_save, sender=BlogPost)
def blog_post_published(sender, instance, created, **kwargs):
    """Handle blog post publication"""
    if instance.status == 'published' and instance.published_date:
        # Award achievement for first published post
        if not created and BlogPost.objects.filter(
            author=instance.author, 
            status='published'
        ).count() == 1:
            UserAchievement.objects.create(
                user=instance.author,
                title='First Blog Post',
                description='Published your first blog post',
                achievement_type='special_recognition',
                points_awarded=50,
                badge_icon='fas fa-pen'
            )
            
            # Award points
            instance.author.add_points(50)
        
        # Award points for publishing
        if not created:  # Only for newly published posts, not new posts
            instance.author.add_points(25)
        
        # Log activity
        UserActivity.objects.create(
            user=instance.author,
            activity_type='blog_post',
            description=f'Published blog post: {instance.title}'
        )
        
        # Check for prolific writer achievements
        published_count = BlogPost.objects.filter(
            author=instance.author,
            status='published'
        ).count()
        
        achievements = [
            (5, 'Prolific Writer', 'Published 5 blog posts'),
            (10, 'Content Creator', 'Published 10 blog posts'),
            (25, 'Blog Master', 'Published 25 blog posts'),
            (50, 'Content Guru', 'Published 50 blog posts'),
        ]
        
        for threshold, title, description in achievements:
            if published_count == threshold:
                UserAchievement.objects.create(
                    user=instance.author,
                    title=title,
                    description=description,
                    achievement_type='points_milestone',
                    points_awarded=threshold * 10,
                    badge_icon='fas fa-trophy'
                )
                instance.author.add_points(threshold * 10)
                break

@receiver(post_save, sender=BlogComment)
def blog_comment_posted(sender, instance, created, **kwargs):
    """Handle new blog comment"""
    if created:
        # Award points for commenting
        instance.author.add_points(5)
        
        # Log activity
        UserActivity.objects.create(
            user=instance.author,
            activity_type='comment',
            description=f'Commented on: {instance.post.title}'
        )
        
        # Notify post author (if different from commenter)
        if instance.post.author != instance.author:
            UserNotification.objects.create(
                user=instance.post.author,
                title='New Comment on Your Post',
                message=f'{instance.author.get_full_name()} commented on "{instance.post.title}"',
                notification_type='comment'
            )
        
        # Notify parent comment author (for replies)
        if instance.parent and instance.parent.author != instance.author:
            UserNotification.objects.create(
                user=instance.parent.author,
                title='Reply to Your Comment',
                message=f'{instance.author.get_full_name()} replied to your comment on "{instance.post.title}"',
                notification_type='comment'
            )
        
        # Check for active commenter achievements
        comment_count = BlogComment.objects.filter(
            author=instance.author,
            is_approved=True
        ).count()
        
        achievements = [
            (10, 'Active Commenter', 'Made 10 comments'),
            (25, 'Community Contributor', 'Made 25 comments'),
            (50, 'Discussion Leader', 'Made 50 comments'),
            (100, 'Community Champion', 'Made 100 comments'),
        ]
        
        for threshold, title, description in achievements:
            if comment_count == threshold:
                UserAchievement.objects.create(
                    user=instance.author,
                    title=title,
                    description=description,
                    achievement_type='points_milestone',
                    points_awarded=threshold,
                    badge_icon='fas fa-comments'
                )
                instance.author.add_points(threshold)
                break

@receiver(post_save, sender=BlogComment)
def comment_approved(sender, instance, **kwargs):
    """Handle comment approval"""
    if instance.is_approved and not getattr(instance, '_approval_processed', False):
        # Prevent duplicate processing
        instance._approval_processed = True
        
        # Notify commenter about approval
        UserNotification.objects.create(
            user=instance.author,
            title='Comment Approved',
            message=f'Your comment on "{instance.post.title}" has been approved and is now visible.',
            notification_type='comment'
        )

@receiver(post_save, sender=Newsletter)
def newsletter_subscribed(sender, instance, created, **kwargs):
    """Handle newsletter subscription"""
    if created:
        # Create welcome notification if user is logged in
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=instance.email)
            UserNotification.objects.create(
                user=user,
                title='Newsletter Subscription Confirmed',
                message='You have successfully subscribed to our newsletter!',
                notification_type='system_update'
            )
            
            # Award points for newsletter subscription
            user.add_points(5)
            
            # Log activity
            UserActivity.objects.create(
                user=user,
                activity_type='newsletter_subscription',
                description='Subscribed to newsletter'
            )
        except User.DoesNotExist:
            # Email not associated with any user account
            pass

# Auto-approve comments from verified users
@receiver(pre_save, sender=BlogComment)
def auto_approve_verified_comments(sender, instance, **kwargs):
    """Auto-approve comments from verified users"""
    if instance.author and instance.author.is_verified:
        instance.is_approved = True