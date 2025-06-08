from django.utils import timezone
from django.db.models import Q
from .models import SiteSettings, Announcement
from services.models import CompanyInfo, ServiceCategory
from blog.models import BlogCategory

def global_context(request):
    """Add global context variables to all templates"""
    
    # Get site settings
    try:
        site_settings = SiteSettings.objects.first()
    except SiteSettings.DoesNotExist:
        site_settings = None
    
    # Get company info
    try:
        company_info = CompanyInfo.objects.first()
    except CompanyInfo.DoesNotExist:
        company_info = None
    
    # Get current announcements for the user
    current_announcements = []
    if request.user.is_authenticated:
        current_announcements = Announcement.objects.filter(
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        )
        
        # Filter by user type if targeting is set
        if hasattr(request.user, 'user_type'):
            user_type = request.user.user_type
            current_announcements = current_announcements.filter(
                Q(target_user_types__icontains=user_type) | 
                Q(target_user_types='') | 
                Q(show_to_all_users=True)
            )
    else:
        # Show announcements for non-logged-in users
        current_announcements = Announcement.objects.filter(
            is_active=True,
            show_to_all_users=True,
            show_to_logged_in_only=False,
            start_date__lte=timezone.now()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        )
    
    # Get service categories for navigation
    service_categories = ServiceCategory.objects.filter(is_active=True)[:6]
    
    # Get blog categories for navigation
    blog_categories = BlogCategory.objects.filter(is_active=True)[:5]
    
    # Get user's unread notifications count
    unread_notifications_count = 0
    if request.user.is_authenticated and hasattr(request.user, 'notifications'):
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
    
    # Current year for footer
    current_year = timezone.now().year
    
    # Navigation items
    main_navigation = [
        {'name': 'Home', 'url': '/', 'icon': 'fas fa-home'},
        {'name': 'Services', 'url': '/services/', 'icon': 'fas fa-cogs'},
        {'name': 'About', 'url': '/about/', 'icon': 'fas fa-info-circle'},
        {'name': 'Blog', 'url': '/blog/', 'icon': 'fas fa-blog'},
        {'name': 'Contact', 'url': '/contact/', 'icon': 'fas fa-envelope'},
    ]
    
    # User navigation (for authenticated users)
    user_navigation = []
    if request.user.is_authenticated:
        user_navigation = [
            {'name': 'Dashboard', 'url': '/dashboard/', 'icon': 'fas fa-tachometer-alt'},
            {'name': 'My Courses', 'url': '/dashboard/courses/', 'icon': 'fas fa-graduation-cap'},
            {'name': 'Profile', 'url': '/dashboard/profile/', 'icon': 'fas fa-user'},
        ]
        
        if request.user.user_type == 'developer':
            user_navigation.extend([
                {'name': 'My Tasks', 'url': '/dashboard/tasks/', 'icon': 'fas fa-tasks'},
                {'name': 'Portfolio', 'url': '/dashboard/portfolio/', 'icon': 'fas fa-briefcase'},
            ])
        
        if request.user.is_staff:
            user_navigation.append(
                {'name': 'Admin Panel', 'url': '/admin/', 'icon': 'fas fa-cog'}
            )
    
    # Social media links
    social_links = []
    if site_settings:
        if site_settings.facebook_url:
            social_links.append({'name': 'Facebook', 'url': site_settings.facebook_url, 'icon': 'fab fa-facebook-f'})
        if site_settings.twitter_url:
            social_links.append({'name': 'Twitter', 'url': site_settings.twitter_url, 'icon': 'fab fa-twitter'})
        if site_settings.linkedin_url:
            social_links.append({'name': 'LinkedIn', 'url': site_settings.linkedin_url, 'icon': 'fab fa-linkedin-in'})
        if site_settings.instagram_url:
            social_links.append({'name': 'Instagram', 'url': site_settings.instagram_url, 'icon': 'fab fa-instagram'})
        if site_settings.youtube_url:
            social_links.append({'name': 'YouTube', 'url': site_settings.youtube_url, 'icon': 'fab fa-youtube'})
    
    # Check if site is in maintenance mode
    maintenance_mode = site_settings.maintenance_mode if site_settings else False
    
    return {
        'site_settings': site_settings,
        'company_info': company_info,
        'current_announcements': current_announcements,
        'service_categories': service_categories,
        'blog_categories': blog_categories,
        'unread_notifications_count': unread_notifications_count,
        'current_year': current_year,
        'main_navigation': main_navigation,
        'user_navigation': user_navigation,
        'social_links': social_links,
        'maintenance_mode': maintenance_mode,
        'request_path': request.path,
    }