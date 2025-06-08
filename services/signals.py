from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Enrollment, Task, TaskApplication, TaskSubmission, ServiceReview
from accounts.models import UserNotification, UserAchievement
from dashboard.models import UserActivity

@receiver(post_save, sender=Enrollment)
def enrollment_created(sender, instance, created, **kwargs):
    """Handle new enrollment"""
    if created:
        # Create notification
        UserNotification.objects.create(
            user=instance.user,
            title='Course Enrollment Confirmed',
            message=f'You have successfully enrolled in {instance.course.service.title}',
            notification_type='course_enrolled'
        )
        
        # Award points for enrollment
        instance.user.add_points(20)
        
        # Log activity
        UserActivity.objects.create(
            user=instance.user,
            activity_type='course_enrollment',
            description=f'Enrolled in {instance.course.service.title}'
        )
        
        # Send welcome email to student
        send_enrollment_welcome_email(instance)
        
        # Notify instructor
        if instance.course.instructor:
            UserNotification.objects.create(
                user=instance.course.instructor,
                title='New Student Enrollment',
                message=f'{instance.user.get_full_name()} enrolled in {instance.course.service.title}',
                notification_type='course_enrolled'
            )

@receiver(post_save, sender=Enrollment)
def enrollment_completed(sender, instance, **kwargs):
    """Handle enrollment completion"""
    if instance.status == 'completed' and instance.completion_date:
        # Award completion achievement
        UserAchievement.objects.get_or_create(
            user=instance.user,
            title=f'Completed: {instance.course.service.title}',
            defaults={
                'description': f'Successfully completed the {instance.course.service.title} course',
                'achievement_type': 'course_completion',
                'points_awarded': 100,
                'badge_icon': 'fas fa-graduation-cap'
            }
        )
        
        # Award completion points
        instance.user.add_points(100)
        
        # Create notification
        UserNotification.objects.create(
            user=instance.user,
            title='Course Completed!',
            message=f'Congratulations! You have completed {instance.course.service.title}',
            notification_type='course_completed'
        )
        
        # Log activity
        UserActivity.objects.create(
            user=instance.user,
            activity_type='course_completion',
            description=f'Completed course: {instance.course.service.title}'
        )

@receiver(post_save, sender=Task)
def task_assigned(sender, instance, **kwargs):
    """Handle task assignment"""
    if instance.assigned_to and instance.status == 'assigned':
        # Create notification for assigned developer
        UserNotification.objects.create(
            user=instance.assigned_to,
            title='New Task Assigned',
            message=f'You have been assigned a new task: {instance.title}',
            notification_type='task_assigned'
        )
        
        # Log activity
        UserActivity.objects.create(
            user=instance.assigned_to,
            activity_type='task_assigned',
            description=f'Assigned to task: {instance.title}'
        )
        
        # Send email notification
        send_task_assignment_email(instance)

@receiver(post_save, sender=TaskApplication)
def task_application_submitted(sender, instance, created, **kwargs):
    """Handle new task application"""
    if created:
        # Notify task owner
        UserNotification.objects.create(
            user=instance.task.assigned_by,
            title='New Task Application',
            message=f'{instance.applicant.get_full_name()} applied for task: {instance.task.title}',
            notification_type='task_application'
        )
        
        # Log activity for applicant
        UserActivity.objects.create(
            user=instance.applicant,
            activity_type='task_application',
            description=f'Applied for task: {instance.task.title}'
        )

@receiver(post_save, sender=TaskApplication)
def task_application_reviewed(sender, instance, **kwargs):
    """Handle task application review"""
    if instance.status in ['accepted', 'rejected'] and instance.reviewed_date:
        # Notify applicant
        if instance.status == 'accepted':
            message = f'Your application for "{instance.task.title}" has been accepted!'
            # Assign the task
            instance.task.assigned_to = instance.applicant
            instance.task.status = 'assigned'
            instance.task.assigned_date = timezone.now()
            instance.task.save()
        else:
            message = f'Your application for "{instance.task.title}" was not accepted this time.'
        
        UserNotification.objects.create(
            user=instance.applicant,
            title='Application Update',
            message=message,
            notification_type='task_application'
        )

@receiver(post_save, sender=TaskSubmission)
def task_submitted(sender, instance, created, **kwargs):
    """Handle task submission"""
    if created:
        # Notify task owner
        UserNotification.objects.create(
            user=instance.task.assigned_by,
            title='Task Submitted',
            message=f'{instance.submitted_by.get_full_name()} submitted work for: {instance.task.title}',
            notification_type='task_submission'
        )
        
        # Update task status
        instance.task.status = 'review'
        instance.task.save()
        
        # Log activity
        UserActivity.objects.create(
            user=instance.submitted_by,
            activity_type='task_submission',
            description=f'Submitted work for task: {instance.task.title}'
        )

@receiver(post_save, sender=TaskSubmission)
def task_submission_reviewed(sender, instance, **kwargs):
    """Handle task submission review"""
    if instance.is_approved and instance.reviewed_date:
        # Mark task as completed
        task = instance.task
        task.status = 'completed'
        task.completed_date = timezone.now()
        task.save()
        
        # Award points and payment to developer
        developer = task.assigned_to
        developer.add_points(task.points_reward)
        
        # Create completion achievement
        UserAchievement.objects.create(
            user=developer,
            title='Task Completed',
            description=f'Successfully completed task: {task.title}',
            achievement_type='project_completion',
            points_awarded=task.points_reward,
            badge_icon='fas fa-check-circle'
        )
        
        # Notify developer
        UserNotification.objects.create(
            user=developer,
            title='Task Approved!',
            message=f'Your work on "{task.title}" has been approved! You earned {task.points_reward} points.',
            notification_type='task_completed'
        )
        
        # Log activity
        UserActivity.objects.create(
            user=developer,
            activity_type='task_completion',
            description=f'Completed task: {task.title}'
        )

@receiver(post_save, sender=ServiceReview)
def service_review_submitted(sender, instance, created, **kwargs):
    """Handle new service review"""
    if created:
        # Award points for reviewing
        instance.user.add_points(10)
        
        # Log activity
        UserActivity.objects.create(
            user=instance.user,
            activity_type='review_posted',
            description=f'Reviewed service: {instance.service.title}'
        )
        
        # Update service average rating
        from django.db.models import Avg
        avg_rating = ServiceReview.objects.filter(
            service=instance.service,
            is_verified=True
        ).aggregate(avg=Avg('rating'))['avg']
        
        instance.service.average_rating = avg_rating or 0
        instance.service.save()

def send_enrollment_welcome_email(enrollment):
    """Send welcome email to newly enrolled student"""
    try:
        subject = f'Welcome to {enrollment.course.service.title}!'
        message = f'''
        Dear {enrollment.user.get_full_name()},
        
        Welcome to {enrollment.course.service.title}!
        
        Course Details:
        - Instructor: {enrollment.course.instructor.get_full_name() if enrollment.course.instructor else 'TBA'}
        - Start Date: {enrollment.course.start_date}
        - Duration: {enrollment.course.service.duration_weeks} weeks
        
        You can access your course materials and track your progress in your dashboard.
        
        Best regards,
        The Debsploit Solutions Team
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[enrollment.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send enrollment welcome email: {e}")

def send_task_assignment_email(task):
    """Send email notification for task assignment"""
    try:
        subject = f'New Task Assigned: {task.title}'
        message = f'''
        Dear {task.assigned_to.get_full_name()},
        
        You have been assigned a new task: {task.title}
        
        Task Details:
        - Due Date: {task.due_date}
        - Budget: {task.budget} {task.currency if hasattr(task, 'currency') else 'KES'}
        - Points Reward: {task.points_reward}
        
        Description:
        {task.description}
        
        Please log into your dashboard to view full details and start working on this task.
        
        Best regards,
        The Debsploit Solutions Team
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.assigned_to.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send task assignment email: {e}")