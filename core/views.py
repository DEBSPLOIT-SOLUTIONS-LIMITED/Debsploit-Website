from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

from .models import (
    SiteSettings, HeroSection, CompanyStatistic, PageContent, 
    TeamMember, Announcement, SiteAnalytics
)
from services.models import Service, ServiceCategory, CompanyInfo
from blog.models import BlogPost, BlogCategory, Newsletter, ContactMessage, FAQ, Testimonial
from accounts.models import User

class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get site settings
        try:
            site_settings = SiteSettings.objects.first()
        except SiteSettings.DoesNotExist:
            site_settings = None
        
        # Get hero sections
        hero_sections = HeroSection.objects.filter(is_active=True)
        
        # Get featured services
        featured_services = Service.objects.filter(
            is_active=True, 
            is_featured=True
        )[:6]
        
        # Get service categories
        service_categories = ServiceCategory.objects.filter(is_active=True)
        
        # Get company statistics
        company_stats = CompanyStatistic.objects.filter(is_active=True)
        
        # Get featured blog posts
        featured_blog_posts = BlogPost.objects.filter(
            status='published',
            is_featured=True
        )[:3]
        
        # Get testimonials
        testimonials = Testimonial.objects.filter(
            is_approved=True,
            is_featured=True
        )[:6]
        
        # Get team members
        team_members = TeamMember.objects.filter(
            is_active=True,
            is_featured=True
        )[:8]
        
        # Get current announcements
        current_announcements = Announcement.objects.filter(
            is_active=True,
            show_on_homepage=True,
            start_date__lte=timezone.now()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        )
        
        # Get company info
        try:
            company_info = CompanyInfo.objects.first()
        except CompanyInfo.DoesNotExist:
            company_info = None
        
        context.update({
            'site_settings': site_settings,
            'hero_sections': hero_sections,
            'featured_services': featured_services,
            'service_categories': service_categories,
            'company_stats': company_stats,
            'featured_blog_posts': featured_blog_posts,
            'testimonials': testimonials,
            'team_members': team_members,
            'current_announcements': current_announcements,
            'company_info': company_info,
        })
        
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get about page content
        try:
            about_content = PageContent.objects.get(page_type='about', is_published=True)
        except PageContent.DoesNotExist:
            about_content = None
        
        # Get all team members
        team_members = TeamMember.objects.filter(is_active=True)
        
        # Get company statistics
        company_stats = CompanyStatistic.objects.filter(is_active=True)
        
        # Get testimonials
        testimonials = Testimonial.objects.filter(is_approved=True)[:10]
        
        context.update({
            'about_content': about_content,
            'team_members': team_members,
            'company_stats': company_stats,
            'testimonials': testimonials,
        })
        
        return context

class ServicesView(ListView):
    model = Service
    template_name = 'core/services.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        
        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by service type
        service_type = self.request.GET.get('type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        # Filter by difficulty level
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['price', '-price', 'title', '-title', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get services page content
        try:
            services_content = PageContent.objects.get(page_type='services', is_published=True)
        except PageContent.DoesNotExist:
            services_content = None
        
        # Get service categories for filtering
        service_categories = ServiceCategory.objects.filter(is_active=True)
        
        # Get current filters
        current_filters = {
            'category': self.request.GET.get('category'),
            'type': self.request.GET.get('type'),
            'difficulty': self.request.GET.get('difficulty'),
            'search': self.request.GET.get('search'),
            'sort': self.request.GET.get('sort', '-created_at'),
        }
        
        context.update({
            'services_content': services_content,
            'service_categories': service_categories,
            'current_filters': current_filters,
            'service_types': Service.SERVICE_TYPES,
            'difficulty_levels': Service.DIFFICULTY_LEVELS,
        })
        
        return context

class ContactView(TemplateView):
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get contact page content
        try:
            contact_content = PageContent.objects.get(page_type='contact', is_published=True)
        except PageContent.DoesNotExist:
            contact_content = None
        
        # Get company info
        try:
            company_info = CompanyInfo.objects.first()
        except CompanyInfo.DoesNotExist:
            company_info = None
        
        # Get FAQs
        faqs = FAQ.objects.filter(is_active=True)
        
        context.update({
            'contact_content': contact_content,
            'company_info': company_info,
            'faqs': faqs,
            'subject_choices': ContactMessage.SUBJECT_CHOICES,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle contact form submission"""
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone', '')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            
            # Validate required fields
            if not all([name, email, subject, message]):
                messages.error(request, 'Please fill in all required fields.')
                return self.get(request, *args, **kwargs)
            
            # Create contact message
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            
            # Send notification email to admin
            try:
                admin_email = settings.DEFAULT_FROM_EMAIL
                send_mail(
                    subject=f'New Contact Message: {subject}',
                    message=f'Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}',
                    from_email=email,
                    recipient_list=[admin_email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
            
            messages.success(request, 'Thank you for your message! We\'ll get back to you soon.')
            return redirect('core:contact')
            
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again.')
            return self.get(request, *args, **kwargs)

@csrf_exempt
@require_http_methods(["POST"])
def newsletter_signup(request):
    """Handle newsletter signup via AJAX"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        name = data.get('name', '')
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'})
        
        # Check if email already exists
        if Newsletter.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already subscribed.'})
        
        # Create newsletter subscription
        Newsletter.objects.create(email=email, name=name)
        
        # Send welcome email (optional)
        try:
            send_mail(
                subject='Welcome to Debsploit Solutions Newsletter!',
                message=f'Hi {name or "there"},\n\nThank you for subscribing to our newsletter. You\'ll receive updates about our latest courses, services, and tech insights.\n\nBest regards,\nDebsploit Solutions Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except:
            pass
        
        return JsonResponse({'success': True, 'message': 'Successfully subscribed to newsletter!'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})

class TeamView(ListView):
    model = TeamMember
    template_name = 'core/team.html'
    context_object_name = 'team_members'
    
    def get_queryset(self):
        return TeamMember.objects.filter(is_active=True)

class PageDetailView(DetailView):
    model = PageContent
    template_name = 'core/page_detail.html'
    context_object_name = 'page'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return PageContent.objects.filter(is_published=True)

def search_view(request):
    """Global search functionality"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        # Search in services
        services = Service.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:5]
        
        for service in services:
            results.append({
                'type': 'Service',
                'title': service.title,
                'description': service.description[:150] + '...' if len(service.description) > 150 else service.description,
                'url': service.get_absolute_url(),
                'category': service.category.name
            })
        
        # Search in blog posts
        blog_posts = BlogPost.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            status='published'
        )[:5]
        
        for post in blog_posts:
            results.append({
                'type': 'Blog Post',
                'title': post.title,
                'description': post.excerpt[:150] + '...' if len(post.excerpt) > 150 else post.excerpt,
                'url': post.get_absolute_url(),
                'category': post.category.name
            })
        
        # Search in pages
        pages = PageContent.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_published=True
        )[:3]
        
        for page in pages:
            results.append({
                'type': 'Page',
                'title': page.title,
                'description': page.subtitle or '',
                'url': f'/page/{page.slug}/',
                'category': page.get_page_type_display()
            })
    
    context = {
        'query': query,
        'results': results,
        'total_results': len(results)
    }
    
    return render(request, 'core/search_results.html', context)

@login_required
def update_analytics(request):
    """Update site analytics (for admin use)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        today = timezone.now().date()
        analytics, created = SiteAnalytics.objects.get_or_create(date=today)
        
        # Update basic stats
        analytics.total_page_views += 1
        analytics.unique_visitors = User.objects.filter(
            last_login__date=today
        ).count()
        analytics.new_registrations = User.objects.filter(
            date_joined__date=today
        ).count()
        
        analytics.save()
        
        return JsonResponse({'success': True, 'message': 'Analytics updated'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def sitemap_view(request):
    """Generate XML sitemap"""
    from django.contrib.sitemaps import Sitemap
    from django.urls import reverse
    
    # This is a basic implementation - you'd want to use django.contrib.sitemaps
    # for a full implementation
    urls = []
    
    # Add static pages
    static_pages = ['core:home', 'core:about', 'core:services', 'core:contact']
    for page in static_pages:
        urls.append({
            'location': request.build_absolute_uri(reverse(page)),
            'lastmod': timezone.now().date(),
            'changefreq': 'weekly',
            'priority': '0.8'
        })
    
    # Add services
    services = Service.objects.filter(is_active=True)
    for service in services:
        urls.append({
            'location': request.build_absolute_uri(service.get_absolute_url()),
            'lastmod': service.updated_at.date(),
            'changefreq': 'monthly',
            'priority': '0.6'
        })
    
    # Add blog posts
    blog_posts = BlogPost.objects.filter(status='published')
    for post in blog_posts:
        urls.append({
            'location': request.build_absolute_uri(post.get_absolute_url()),
            'lastmod': post.updated_at.date(),
            'changefreq': 'monthly',
            'priority': '0.5'
        })
    
    context = {'urls': urls}
    return render(request, 'core/sitemap.xml', context, content_type='application/xml')

def robots_txt_view(request):
    """Generate robots.txt"""
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
        "",
        "# Disallow admin and private areas",
        "Disallow: /admin/",
        "Disallow: /dashboard/private/",
        "Disallow: /api/private/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")