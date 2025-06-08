from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db import models

from .models import (
    BlogPost, BlogCategory, BlogComment, BlogTag, Newsletter,
    ContactMessage, FAQ, Testimonial
)
from .forms import (
    BlogPostForm, BlogCommentForm, ContactForm, NewsletterForm,
    FAQForm, TestimonialForm, BlogSearchForm
)
from accounts.models import UserNotification
from dashboard.models import UserActivity

class BlogPostListView(ListView):
    """List all published blog posts"""
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(
            status='published',
            published_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query)
            )
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by tag
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Filter by author
        author_id = self.request.GET.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-published_date')
        if sort_by in ['-published_date', 'published_date', '-views_count', 'title', '-title']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured posts
        context['featured_posts'] = BlogPost.objects.filter(
            status='published',
            is_featured=True,
            published_date__lte=timezone.now()
        )[:3]
        
        # Categories
        context['categories'] = BlogCategory.objects.filter(is_active=True).annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )
        
        # Popular tags
        context['popular_tags'] = BlogTag.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).filter(post_count__gt=0).order_by('-post_count')[:10]
        
        # Recent posts sidebar
        context['recent_posts'] = BlogPost.objects.filter(
            status='published',
            published_date__lte=timezone.now()
        ).order_by('-published_date')[:5]
        
        # Current filters
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'category': self.request.GET.get('category', ''),
            'tag': self.request.GET.get('tag', ''),
            'author': self.request.GET.get('author', ''),
            'sort': self.request.GET.get('sort', '-published_date'),
        }
        
        return context

class BlogPostDetailView(DetailView):
    """Detailed view of a blog post"""
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        queryset = BlogPost.objects.select_related('author', 'category').prefetch_related('tags')
        
        # Allow authors and staff to view unpublished posts
        if self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            BlogPost.objects.filter(slug=self.kwargs['slug'], author=self.request.user).exists()
        ):
            return queryset
        
        # Public users only see published posts
        return queryset.filter(
            status='published',
            published_date__lte=timezone.now()
        )
    
    def get_object(self):
        post = super().get_object()
        
        # Increment view count
        BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        post.refresh_from_db()
        
        return post
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Comments
        comments = BlogComment.objects.filter(
            post=post,
            parent__isnull=True,
            is_approved=True
        ).select_related('author').order_by('-created_at')
        
        context['comments'] = comments
        context['comments_count'] = BlogComment.objects.filter(
            post=post,
            is_approved=True
        ).count()
        
        # Comment form
        if self.request.user.is_authenticated:
            context['comment_form'] = BlogCommentForm()
        
        # Related posts
        context['related_posts'] = BlogPost.objects.filter(
            category=post.category,
            status='published',
            published_date__lte=timezone.now()
        ).exclude(id=post.id)[:4]
        
        # Previous and next posts
        context['previous_post'] = BlogPost.objects.filter(
            status='published',
            published_date__lt=post.published_date
        ).order_by('-published_date').first()
        
        context['next_post'] = BlogPost.objects.filter(
            status='published',
            published_date__gt=post.published_date
        ).order_by('published_date').first()
        
        return context

class BlogCategoryView(ListView):
    """List posts by category"""
    model = BlogPost
    template_name = 'blog/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.category = get_object_or_404(
            BlogCategory,
            slug=self.kwargs['slug'],
            is_active=True
        )
        return BlogPost.objects.filter(
            category=self.category,
            status='published',
            published_date__lte=timezone.now()
        ).select_related('author').order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['all_categories'] = BlogCategory.objects.filter(is_active=True)
        return context

class BlogTagView(ListView):
    """List posts by tag"""
    model = BlogPost
    template_name = 'blog/tag_posts.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.tag = get_object_or_404(BlogTag, slug=self.kwargs['slug'])
        return BlogPost.objects.filter(
            tags=self.tag,
            status='published',
            published_date__lte=timezone.now()
        ).select_related('author', 'category').order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

class BlogPostCreateView(LoginRequiredMixin, CreateView):
    """Create a new blog post"""
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/post_create.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        # Set published date if publishing
        if form.instance.status == 'published' and not form.instance.published_date:
            form.instance.published_date = timezone.now()
        
        response = super().form_valid(form)
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='blog_post',
            description=f'Created blog post: {self.object.title}'
        )
        
        messages.success(self.request, 'Blog post created successfully!')
        return response
    
    def get_success_url(self):
        return self.object.get_absolute_url()

class BlogPostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a blog post"""
    model = BlogPost
    form_class = BlogPostForm
    template_name = 'blog/post_update.html'
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def form_valid(self, form):
        # Set published date if publishing for the first time
        if (form.instance.status == 'published' and 
            not form.instance.published_date):
            form.instance.published_date = timezone.now()
        
        response = super().form_valid(form)
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='blog_post',
            description=f'Updated blog post: {self.object.title}'
        )
        
        messages.success(self.request, 'Blog post updated successfully!')
        return response

class BlogPostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a blog post"""
    model = BlogPost
    template_name = 'blog/post_delete.html'
    success_url = reverse_lazy('blog:post_list')
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post_title = post.title
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='blog_post',
            description=f'Deleted blog post: {post_title}'
        )
        
        messages.success(request, f'Blog post "{post_title}" deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
@require_http_methods(["POST"])
def add_comment(request, post_slug):
    """Add a comment to a blog post"""
    post = get_object_or_404(
        BlogPost,
        slug=post_slug,
        status='published',
        published_date__lte=timezone.now()
    )
    
    if not post.allow_comments:
        return JsonResponse({
            'success': False,
            'error': 'Comments are disabled for this post.'
        })
    
    form = BlogCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        
        # Check for parent comment (replies)
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = BlogComment.objects.get(id=parent_id, post=post)
                comment.parent = parent_comment
            except BlogComment.DoesNotExist:
                pass
        
        comment.save()
        
        # Notify post author
        if post.author != request.user:
            UserNotification.objects.create(
                user=post.author,
                title='New Comment on Your Post',
                message=f'{request.user.get_full_name()} commented on "{post.title}"',
                notification_type='comment'
            )
        
        # Award points for commenting
        request.user.add_points(5)
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='comment',
            description=f'Commented on blog post: {post.title}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully!',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author_name': comment.author.get_full_name(),
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_approved': comment.is_approved,
            }
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    })

def contact_view(request):
    """Handle contact form submissions"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            
            # Send notification email to admin
            try:
                send_mail(
                    subject=f'New Contact Message: {contact_message.get_subject_display()}',
                    message=f'''
                    New contact message received:
                    
                    Name: {contact_message.name}
                    Email: {contact_message.email}
                    Phone: {contact_message.phone}
                    Subject: {contact_message.get_subject_display()}
                    
                    Message:
                    {contact_message.message}
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send contact notification email: {e}")
            
            messages.success(request, 'Thank you for your message! We\'ll get back to you soon.')
            return redirect('blog:contact')
    else:
        form = ContactForm()
    
    # Get FAQs
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
    faq_categories = {}
    for faq in faqs:
        category = faq.get_category_display()
        if category not in faq_categories:
            faq_categories[category] = []
        faq_categories[category].append(faq)
    
    context = {
        'form': form,
        'faq_categories': faq_categories,
    }
    
    return render(request, 'blog/contact.html', context)

@require_http_methods(["POST"])
def newsletter_signup(request):
    """Handle newsletter signup"""
    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name', '')
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email is required.'
            })
        
        # Check if email already exists
        if Newsletter.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already subscribed to newsletter.'
            })
        
        # Create newsletter subscription
        Newsletter.objects.create(email=email, name=name)
        
        # Send welcome email
        try:
            send_mail(
                subject='Welcome to Debsploit Solutions Newsletter!',
                message=f'''
                Hi {name or "there"},
                
                Thank you for subscribing to our newsletter! You'll receive updates about:
                - New courses and training programs
                - Industry insights and tech trends
                - Special offers and promotions
                - Community events and workshops
                
                Best regards,
                The Debsploit Solutions Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send newsletter welcome email: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully subscribed to newsletter!'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })

class TestimonialListView(ListView):
    """List approved testimonials"""
    model = Testimonial
    template_name = 'blog/testimonials.html'
    context_object_name = 'testimonials'
    paginate_by = 12
    
    def get_queryset(self):
        return Testimonial.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')

def blog_search(request):
    """AJAX blog search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    posts = BlogPost.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(excerpt__icontains=query),
        status='published',
        published_date__lte=timezone.now()
    ).select_related('author', 'category')[:10]
    
    results = [
        {
            'id': post.id,
            'title': post.title,
            'excerpt': post.excerpt,
            'author': post.author.get_full_name(),
            'category': post.category.name,
            'published_date': post.published_date.strftime('%B %d, %Y'),
            'reading_time': post.reading_time,
            'url': post.get_absolute_url(),
            'featured_image': post.featured_image.url if post.featured_image else None,
        }
        for post in posts
    ]
    
    return JsonResponse({'results': results})

def archive_view(request):
    """Blog archive by month/year"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    posts = BlogPost.objects.filter(
        status='published',
        published_date__lte=timezone.now()
    ).select_related('author', 'category')
    
    if year:
        posts = posts.filter(published_date__year=year)
    if month:
        posts = posts.filter(published_date__month=month)
    
    posts = posts.order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Archive dates for sidebar
    archive_dates = BlogPost.objects.filter(
        status='published'
    ).dates('published_date', 'month', order='DESC')
    
    context = {
        'posts': page_obj,
        'archive_dates': archive_dates,
        'current_year': year,
        'current_month': month,
    }
    
    return render(request, 'blog/archive.html', context)

def author_posts(request, author_id):
    """List posts by a specific author"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    author = get_object_or_404(User, id=author_id)
    
    posts = BlogPost.objects.filter(
        author=author,
        status='published',
        published_date__lte=timezone.now()
    ).select_related('category').order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Author stats
    author_stats = {
        'total_posts': posts.count(),
        'total_views': posts.aggregate(total_views=models.Sum('views_count'))['total_views'] or 0,
        'member_since': author.date_joined,
    }
    
    context = {
        'author': author,
        'posts': page_obj,
        'author_stats': author_stats,
    }
    
    return render(request, 'blog/author_posts.html', context)