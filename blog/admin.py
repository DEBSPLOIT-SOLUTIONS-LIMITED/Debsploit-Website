# blog/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    BlogCategory, BlogPost, BlogComment, BlogTag, 
    Newsletter, ContactMessage, FAQ, Testimonial
)

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'color_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 50%;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'
    
    def post_count(self, obj):
        count = obj.posts.filter(status='published').count()
        return format_html(
            '<span style="background: #007cba; color: white; padding: 2px 8px; border-radius: 12px;">{}</span>',
            count
        )
    post_count.short_description = 'Published Posts'

class BlogTagInline(admin.TabularInline):
    model = BlogTag.posts.through
    extra = 1
    verbose_name = "Tag"
    verbose_name_plural = "Tags"

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'category', 'status', 'is_featured', 
        'views_count', 'published_date', 'created_at'
    ]
    list_filter = [
        'status', 'is_featured', 'allow_comments', 'category', 
        'created_at', 'published_date', 'author'
    ]
    search_fields = ['title', 'content', 'excerpt', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views_count', 'reading_time', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'category', 'excerpt')
        }),
        ('Content', {
            'fields': ('content', 'featured_image')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('status', 'is_featured', 'allow_comments')
        }),
        ('Statistics', {
            'fields': ('views_count', 'reading_time'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('published_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BlogTagInline]
    
    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']
    
    def publish_posts(self, request, queryset):
        updated = 0
        for post in queryset:
            if post.status != 'published':
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
                post.save()
                updated += 1
        self.message_user(request, f'{updated} posts published successfully.')
    publish_posts.short_description = "Publish selected posts"
    
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} posts unpublished successfully.')
    unpublish_posts.short_description = "Unpublish selected posts"
    
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts featured successfully.')
    feature_posts.short_description = "Feature selected posts"
    
    def unfeature_posts(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} posts unfeatured successfully.')
    unfeature_posts.short_description = "Unfeature selected posts"
    
    def save_model(self, request, obj, form, change):
        # Set author to current user if not set
        if not obj.author_id:
            obj.author = request.user
        
        # Set published date when publishing
        if obj.status == 'published' and not obj.published_date:
            obj.published_date = timezone.now()
        
        super().save_model(request, obj, form, change)

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'content_preview', 'is_approved', 'is_reply', 'created_at']
    list_filter = ['is_approved', 'created_at', 'post__category']
    search_fields = ['content', 'author__first_name', 'author__last_name', 'post__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Reply'
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments approved successfully.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments disapproved successfully.')
    disapprove_comments.short_description = "Disapprove selected comments"

@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
    
    def post_count(self, obj):
        count = obj.posts.filter(status='published').count()
        return count
    post_count.short_description = 'Published Posts'

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'subscribed_date']
    list_filter = ['is_active', 'subscribed_date']
    search_fields = ['email', 'name']
    readonly_fields = ['subscribed_date']
    date_hierarchy = 'subscribed_date'
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriptions activated successfully.')
    activate_subscriptions.short_description = "Activate selected subscriptions"
    
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriptions deactivated successfully.')
    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'subject_display', 'status', 
        'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'subject', 'created_at', 'assigned_to']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Admin Management', {
            'fields': ('status', 'assigned_to', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_in_progress', 'mark_resolved', 'mark_closed']
    
    def subject_display(self, obj):
        return obj.get_subject_display()
    subject_display.short_description = 'Subject'
    
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} messages marked as in progress.')
    mark_in_progress.short_description = "Mark as In Progress"
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} messages marked as resolved.')
    mark_resolved.short_description = "Mark as Resolved"
    
    def mark_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} messages marked as closed.')
    mark_closed.short_description = "Mark as Closed"

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category_display', 'order', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('FAQ Information', {
            'fields': ('question', 'answer', 'category')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Category'

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'title', 'company', 'rating_display', 
        'is_featured', 'is_approved', 'created_at'
    ]
    list_filter = ['rating', 'is_featured', 'is_approved', 'created_at']
    search_fields = ['name', 'title', 'company', 'content']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'title', 'company', 'photo')
        }),
        ('Testimonial', {
            'fields': ('content', 'rating', 'service')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_testimonials', 'disapprove_testimonials', 'feature_testimonials']
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #ffc107;">{}</span>', stars)
    rating_display.short_description = 'Rating'
    
    def approve_testimonials(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} testimonials approved successfully.')
    approve_testimonials.short_description = "Approve selected testimonials"
    
    def disapprove_testimonials(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} testimonials disapproved successfully.')
    disapprove_testimonials.short_description = "Disapprove selected testimonials"
    
    def feature_testimonials(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} testimonials featured successfully.')
    feature_testimonials.short_description = "Feature selected testimonials"