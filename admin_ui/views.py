from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from blog.models import BlogPost, ContactMessage
from services.models import Service

User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard"""
    context = {
        'stats': {
            'total_users': User.objects.count(),
            'total_posts': BlogPost.objects.count(),
            'total_services': Service.objects.count(),
            'pending_contacts': ContactMessage.objects.filter(status='new').count(),
        },
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_posts': BlogPost.objects.order_by('-created_at')[:5],
        'recent_contacts': ContactMessage.objects.order_by('-created_at')[:5],
    }
    return render(request, 'admin_ui/dashboard.html', context)


@staff_member_required
def admin_users(request):
    """Users management"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_ui/users.html', {'users': users})


@staff_member_required
def admin_services(request):
    """Services management"""
    services = Service.objects.all().order_by('-created_at')
    return render(request, 'admin_ui/services.html', {'services': services})


@staff_member_required
def admin_blog(request):
    """Blog management"""
    posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'admin_ui/blog.html', {'posts': posts})


@staff_member_required
def admin_contacts(request):
    """Contact messages management"""
    contacts = ContactMessage.objects.all().order_by('-created_at')
    return render(request, 'admin_ui/contacts.html', {'contacts': contacts})


@staff_member_required
def admin_settings(request):
    """Settings management"""
    return render(request, 'admin_ui/settings.html')
