from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField

User = get_user_model()

class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#0066FF")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Blog Categories"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class BlogPost(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name='posts')
    
    # Content
    excerpt = models.TextField(max_length=300, help_text="Brief description for previews")
    content = RichTextUploadingField()
    featured_image = models.ImageField(upload_to='blog_images/', blank=True)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    
    # Stats
    views_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=5, help_text="Estimated reading time in minutes")
    
    # Dates
    published_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_date', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-calculate reading time based on content length
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)  # 200 words per minute
        
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_date

class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='replies')
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.post.title}"
    
    @property
    def is_reply(self):
        return self.parent is not None

class BlogTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    posts = models.ManyToManyField(BlogPost, related_name='tags', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email

class ContactMessage(models.Model):
    SUBJECT_CHOICES = (
        ('general', 'General Inquiry'),
        ('programming', 'Programming Training'),
        ('design', 'Graphics Design'),
        ('cybersecurity', 'Cybersecurity'),
        ('networking', 'Networking'),
        ('ai', 'AI Training'),
        ('cctv', 'CCTV Installation'),
        ('marketing', 'Digital Marketing'),
        ('consultation', 'Consultation'),
        ('support', 'Technical Support'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Admin fields
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='assigned_messages')
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"

class FAQ(models.Model):
    CATEGORY_CHOICES = (
        ('general', 'General'),
        ('enrollment', 'Enrollment'),
        ('payment', 'Payment'),
        ('technical', 'Technical'),
        ('courses', 'Courses'),
        ('certification', 'Certification'),
    )
    
    question = models.CharField(max_length=300)
    answer = RichTextUploadingField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200, help_text="Job title or role")
    company = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    photo = models.ImageField(upload_to='testimonial_photos/', blank=True)
    
    # Related service (optional)
    service = models.ForeignKey('services.Service', on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='testimonials')
    
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.title}"