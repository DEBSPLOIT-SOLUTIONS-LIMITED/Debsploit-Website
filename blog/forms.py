from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import FormActions, Tab, TabHolder, Alert
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import (
    BlogPost, BlogCategory, BlogComment, BlogTag, Newsletter,
    ContactMessage, FAQ, Testimonial
)

User = get_user_model()

class BlogPostForm(forms.ModelForm):
    """Form for creating and editing blog posts"""
    tags = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., python, django, web development',
            'class': 'form-control'
        })
    )
    
    publish_now = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Check to publish immediately"
    )
    
    schedule_publish = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        help_text="Schedule publication for a future date"
    )
    
    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'category', 'excerpt', 'content', 'featured_image',
            'meta_description', 'meta_keywords', 'status', 'is_featured',
            'allow_comments', 'reading_time', 'tags', 'publish_now', 'schedule_publish'
        ]
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'content': CKEditorUploadingWidget(),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'meta_keywords': forms.TextInput(attrs={
                'placeholder': 'keyword1, keyword2, keyword3',
                'class': 'form-control'
            }),
            'reading_time': forms.NumberInput(attrs={'min': 1, 'max': 60, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        # Populate tags field if editing existing post
        if self.instance and self.instance.pk:
            tags_list = list(self.instance.tags.values_list('name', flat=True))
            self.fields['tags'].initial = ', '.join(tags_list)
            
            # If post is already published, hide publish options
            if self.instance.status == 'published':
                del self.fields['publish_now']
                del self.fields['schedule_publish']
        
        self.helper.layout = Layout(
            Alert(
                content="<i class='fas fa-info-circle me-2'></i>Complete all required fields and preview your post before publishing.",
                css_class="alert-info"
            ),
            TabHolder(
                Tab(
                    'Content',
                    Row(
                        Column('title', css_class='form-group col-md-8 mb-3'),
                        Column('slug', css_class='form-group col-md-4 mb-3'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('category', css_class='form-group col-md-6 mb-3'),
                        Column('status', css_class='form-group col-md-6 mb-3'),
                        css_class='form-row'
                    ),
                    'excerpt',
                    'content',
                    'featured_image',
                ),
                Tab(
                    'SEO & Meta',
                    'meta_description',
                    'meta_keywords',
                    Row(
                        Column('reading_time', css_class='form-group col-md-6 mb-3'),
                        Column('tags', css_class='form-group col-md-6 mb-3'),
                        css_class='form-row'
                    ),
                ),
                Tab(
                    'Settings',
                    Row(
                        Column('is_featured', css_class='form-group col-md-6 mb-3'),
                        Column('allow_comments', css_class='form-group col-md-6 mb-3'),
                        css_class='form-row'
                    ),
                    Div(
                        HTML('<h5>Publishing Options</h5>'),
                        'publish_now',
                        'schedule_publish',
                        css_class='publishing-options'
                    ) if 'publish_now' in self.fields else HTML(''),
                )
            ),
            FormActions(
                Submit('save_draft', 'Save as Draft', css_class='btn btn-secondary btn-lg'),
                Submit('save_publish', 'Save & Publish', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "blog:post_list" %}" class="btn btn-outline-secondary btn-lg ms-2">Cancel</a>')
            )
        )
    
    def clean_tags(self):
        tags_text = self.cleaned_data.get('tags', '')
        if not tags_text:
            return []
        
        # Split and clean tag names
        tag_names = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Validate tag names
        for tag_name in tag_names:
            if len(tag_name) > 50:
                raise ValidationError(f'Tag "{tag_name}" is too long. Maximum 50 characters.')
            if len(tag_name) < 2:
                raise ValidationError(f'Tag "{tag_name}" is too short. Minimum 2 characters.')
        
        return tag_names
    
    def clean_schedule_publish(self):
        schedule_publish = self.cleaned_data.get('schedule_publish')
        if schedule_publish and schedule_publish <= timezone.now():
            raise ValidationError('Scheduled publish date must be in the future.')
        return schedule_publish
    
    def clean(self):
        cleaned_data = super().clean()
        publish_now = cleaned_data.get('publish_now')
        schedule_publish = cleaned_data.get('schedule_publish')
        
        if publish_now and schedule_publish:
            raise ValidationError('Cannot publish now and schedule publish at the same time.')
        
        return cleaned_data
    
    def save(self, commit=True):
        post = super().save(commit=False)
        
        # Handle publishing options
        if self.cleaned_data.get('publish_now'):
            post.status = 'published'
            post.published_date = timezone.now()
        elif self.cleaned_data.get('schedule_publish'):
            post.status = 'draft'  # Will be published later by a scheduled task
            post.published_date = self.cleaned_data['schedule_publish']
        
        if commit:
            post.save()
            self.save_m2m()
            
            # Handle tags
            tag_names = self.cleaned_data.get('tags', [])
            post.tags.clear()
            
            for tag_name in tag_names:
                tag, created = BlogTag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': tag_name.lower().replace(' ', '-')}
                )
                post.tags.add(tag)
        
        return post

class BlogCommentForm(forms.ModelForm):
    """Form for adding comments to blog posts"""
    
    class Meta:
        model = BlogComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts...',
                'class': 'form-control',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'comment-form'
        
        self.helper.layout = Layout(
            'content',
            FormActions(
                Submit('submit', 'Post Comment', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" onclick="cancelComment()">Cancel</button>')
            )
        )
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.strip()) < 10:
            raise ValidationError('Comment must be at least 10 characters long.')
        
        # Basic spam detection
        spam_words = ['spam', 'viagra', 'casino', 'lottery', 'winner']
        content_lower = content.lower()
        for word in spam_words:
            if word in content_lower:
                raise ValidationError('Your comment appears to contain spam content.')
        
        return content

class ContactForm(forms.ModelForm):
    """Enhanced contact form for general inquiries"""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254 700 000 000'
            }),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Please describe your inquiry in detail...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Alert(
                content="<i class='fas fa-envelope me-2'></i>We'll respond to your inquiry within 24 hours.",
                css_class="alert-info"
            ),
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('phone', css_class='form-group col-md-6 mb-3'),
                Column('subject', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'message',
            FormActions(
                Submit('submit', 'Send Message', css_class='btn btn-primary btn-lg'),
                HTML('<button type="reset" class="btn btn-outline-secondary btn-lg ms-2">Clear Form</button>')
            )
        )
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 20:
            raise ValidationError('Please provide more details. Message must be at least 20 characters.')
        return message

class NewsletterForm(forms.ModelForm):
    """Newsletter subscription form with preferences"""
    
    interests = forms.MultipleChoiceField(
        choices=[
            ('programming', 'Programming & Development'),
            ('design', 'Design & UX/UI'),
            ('cybersecurity', 'Cybersecurity'),
            ('ai_ml', 'AI & Machine Learning'),
            ('marketing', 'Digital Marketing'),
            ('business', 'Business & Entrepreneurship'),
            ('career', 'Career Development'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Select topics you're interested in (optional)"
    )
    
    frequency = forms.ChoiceField(
        choices=[
            ('weekly', 'Weekly'),
            ('bi-weekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
        ],
        initial='weekly',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        help_text="How often would you like to receive updates?"
    )
    
    class Meta:
        model = Newsletter
        fields = ['email', 'name', 'interests', 'frequency']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email address',
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'Your name (optional)',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Alert(
                content="<i class='fas fa-paper-plane me-2'></i>Join thousands of professionals getting tech insights!",
                css_class="alert-success"
            ),
            Row(
                Column('email', css_class='form-group col-md-8 mb-3'),
                Column('name', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            Fieldset(
                'Preferences',
                'interests',
                'frequency',
            ),
            FormActions(
                Submit('submit', 'Subscribe Now', css_class='btn btn-primary btn-lg'),
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Newsletter.objects.filter(email=email, is_active=True).exists():
            raise ValidationError('This email is already subscribed to our newsletter.')
        return email

class BlogSearchForm(forms.Form):
    """Advanced form for searching blog posts"""
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search posts, titles, content...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=BlogCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tag = forms.ModelChoiceField(
        queryset=BlogTag.objects.all(),
        required=False,
        empty_label="All Tags",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    author = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="All Authors",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Posts published after this date"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Posts published before this date"
    )
    sort = forms.ChoiceField(
        choices=[
            ('-published_date', 'Newest First'),
            ('published_date', 'Oldest First'),
            ('-views_count', 'Most Popular'),
            ('title', 'Title A-Z'),
            ('-title', 'Title Z-A'),
            ('-created_at', 'Recently Added'),
        ],
        initial='-published_date',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set author queryset to users who have published posts
        self.fields['author'].queryset = User.objects.filter(
            blog_posts__status='published'
        ).distinct().order_by('first_name', 'last_name')
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='col-md-4'),
                Column('category', css_class='col-md-2'),
                Column('tag', css_class='col-md-2'),
                Column('author', css_class='col-md-2'),
                Column('sort', css_class='col-md-2'),
                css_class='form-row'
            ),
            Row(
                Column('date_from', css_class='col-md-6'),
                Column('date_to', css_class='col-md-6'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Search', css_class='btn btn-primary'),
                HTML('<a href="?" class="btn btn-secondary ms-2">Clear Filters</a>')
            )
        )

class FAQForm(forms.ModelForm):
    """Form for creating/editing FAQs"""
    
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'category', 'order', 'is_active']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the frequently asked question'
            }),
            'answer': CKEditorUploadingWidget(),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            'question',
            'answer',
            Row(
                Column('category', css_class='form-group col-md-4 mb-3'),
                Column('order', css_class='form-group col-md-4 mb-3'),
                Column('is_active', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Save FAQ', css_class='btn btn-primary'),
                HTML('<a href="{% url "blog:faq_list" %}" class="btn btn-secondary ms-2">Cancel</a>')
            )
        )

class TestimonialForm(forms.ModelForm):
    """Form for submitting testimonials"""
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the terms and conditions and give permission to use this testimonial"
    )
    
    class Meta:
        model = Testimonial
        fields = ['name', 'title', 'company', 'content', 'rating', 'photo', 'service', 'terms_accepted']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your job title'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name (optional)'}),
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Share your experience with our services...'
            }),
            'rating': forms.Select(choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Alert(
                content="<i class='fas fa-star me-2'></i>Your testimonial helps others discover our services!",
                css_class="alert-info"
            ),
            Fieldset(
                'Personal Information',
                Row(
                    Column('name', css_class='form-group col-md-6 mb-3'),
                    Column('title', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
                Row(
                    Column('company', css_class='form-group col-md-6 mb-3'),
                    Column('photo', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Your Testimonial',
                'content',
                Row(
                    Column('rating', css_class='form-group col-md-6 mb-3'),
                    Column('service', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
            ),
            'terms_accepted',
            FormActions(
                Submit('submit', 'Submit Testimonial', css_class='btn btn-primary btn-lg'),
            )
        )

class BlogCategoryForm(forms.ModelForm):
    """Form for creating/editing blog categories"""
    
    class Meta:
        model = BlogCategory
        fields = ['name', 'slug', 'description', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-8 mb-3'),
                Column('slug', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('color', css_class='form-group col-md-6 mb-3'),
                Column('is_active', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Save Category', css_class='btn btn-primary'),
            )
        )

class CommentModerationForm(forms.ModelForm):
    """Form for moderating comments"""
    
    moderation_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        help_text="Optional note about the moderation decision"
    )
    
    class Meta:
        model = BlogComment
        fields = ['is_approved', 'moderation_note']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            'is_approved',
            'moderation_note',
            FormActions(
                Submit('submit', 'Update Status', css_class='btn btn-primary'),
            )
        )

class BulkCommentForm(forms.Form):
    """Form for bulk comment actions"""
    ACTION_CHOICES = [
        ('', 'Select Action...'),
        ('approve', 'Approve Comments'),
        ('reject', 'Reject Comments'),
        ('delete', 'Delete Comments'),
        ('mark_spam', 'Mark as Spam'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    comment_ids = forms.CharField(widget=forms.HiddenInput())
    confirmation = forms.BooleanField(
        required=True,
        label="I confirm this bulk action"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            'action',
            'comment_ids',
            'confirmation',
            FormActions(
                Submit('submit', 'Apply Action', css_class='btn btn-warning'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancel</button>')
            )
        )

class EmailNewsletterForm(forms.Form):
    """Form for sending newsletters to subscribers"""
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        widget=CKEditorUploadingWidget()
    )
    send_to_all = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Send to all active subscribers"
    )
    test_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Send test email to this address first"
    )
    subscriber_categories = forms.MultipleChoiceField(
        choices=[
            ('programming', 'Programming Enthusiasts'),
            ('design', 'Design Professionals'),
            ('business', 'Business Leaders'),
            ('students', 'Students'),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text="Target specific subscriber categories"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            'subject',
            'content',
            Fieldset(
                'Sending Options',
                'send_to_all',
                'test_email',
                'subscriber_categories',
            ),
            FormActions(
                Submit('send_test', 'Send Test Email', css_class='btn btn-secondary'),
                Submit('send_newsletter', 'Send Newsletter', css_class='btn btn-primary ms-2'),
            )
        )

class ContactMessageFilterForm(forms.Form):
    """Form for filtering contact messages in admin"""
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(ContactMessage.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.ChoiceField(
        choices=[('', 'All Subjects')] + list(ContactMessage.SUBJECT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        empty_label="All Staff",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('status', css_class='col-md-2'),
                Column('subject', css_class='col-md-3'),
                Column('assigned_to', css_class='col-md-3'),
                Column('date_from', css_class='col-md-2'),
                Column('date_to', css_class='col-md-2'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Filter', css_class='btn btn-primary'),
                HTML('<a href="?" class="btn btn-secondary ms-2">Clear</a>')
            )
        )

class BlogAnalyticsForm(forms.Form):
    """Form for blog analytics filtering"""
    date_range = forms.ChoiceField(
        choices=[
            ('7', 'Last 7 days'),
            ('30', 'Last 30 days'),
            ('90', 'Last 3 months'),
            ('365', 'Last year'),
            ('custom', 'Custom range'),
        ],
        initial='30',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=BlogCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('date_range', css_class='col-md-3'),
                Column('start_date', css_class='col-md-3'),
                Column('end_date', css_class='col-md-3'),
                Column('category', css_class='col-md-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Generate Report', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" onclick="exportData()">Export CSV</button>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if date_range == 'custom':
            if not start_date or not end_date:
                raise ValidationError('Start date and end date are required for custom range.')
            if start_date > end_date:
                raise ValidationError('Start date cannot be after end date.')
        
        return cleaned_data

class BlogImportForm(forms.Form):
    """Form for importing blog posts from external sources"""
    import_source = forms.ChoiceField(
        choices=[
            ('wordpress', 'WordPress Export'),
            ('medium', 'Medium Export'),
            ('csv', 'CSV File'),
            ('json', 'JSON File'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    import_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xml,.csv,.json'}),
        help_text="Upload your export file"
    )
    default_category = forms.ModelChoiceField(
        queryset=BlogCategory.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Default category for imported posts"
    )
    default_status = forms.ChoiceField(
        choices=BlogPost.STATUS_CHOICES,
        initial='draft',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Default status for imported posts"
    )
    preserve_dates = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Keep original publication dates"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Alert(
                content="<i class='fas fa-upload me-2'></i>Import posts from external blogging platforms.",
                css_class="alert-warning"
            ),
            'import_source',
            'import_file',
            Row(
                Column('default_category', css_class='col-md-6'),
                Column('default_status', css_class='col-md-6'),
                css_class='form-row'
            ),
            'preserve_dates',
            FormActions(
                Submit('submit', 'Import Posts', css_class='btn btn-primary'),
            )
        )

class SubscriberPreferencesForm(forms.Form):
    """Form for managing subscriber preferences"""
    email_frequency = forms.ChoiceField(
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('bi-weekly', 'Bi-weekly'),
            ('monthly', 'Monthly'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    content_types = forms.MultipleChoiceField(
        choices=[
            ('tutorials', 'Tutorials & How-tos'),
            ('news', 'Industry News'),
            ('case_studies', 'Case Studies'),
            ('interviews', 'Interviews'),
            ('reviews', 'Product Reviews'),
            ('announcements', 'Company Announcements'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select the types of content you want to receive"
    )
    topics = forms.MultipleChoiceField(
        choices=[
            ('web_dev', 'Web Development'),
            ('mobile_dev', 'Mobile Development'),
            ('data_science', 'Data Science'),
            ('ai_ml', 'AI & Machine Learning'),
            ('cybersecurity', 'Cybersecurity'),
            ('devops', 'DevOps'),
            ('design', 'Design'),
            ('business', 'Business & Startup'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Choose your areas of interest"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Email Frequency',
                'email_frequency',
            ),
            Fieldset(
                'Content Preferences',
                'content_types',
            ),
            Fieldset(
                'Topic Interests',
                'topics',
            ),
            FormActions(
                Submit('submit', 'Update Preferences', css_class='btn btn-primary'),
            )
        )

class BlogSEOForm(forms.Form):
    """Form for SEO analysis and suggestions"""
    target_keyword = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your target keyword'
        }),
        help_text="Main keyword you want to optimize for"
    )
    focus_keywords = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'secondary keyword, related term, synonym'
        }),
        help_text="Additional keywords (comma-separated)"
    )
    competitor_urls = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'https://example.com/competing-article'
        }),
        help_text="URLs of competing articles (one per line)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Alert(
                content="<i class='fas fa-search me-2'></i>Analyze your content for SEO optimization.",
                css_class="alert-info"
            ),
            'target_keyword',
            'focus_keywords',
            'competitor_urls',
            FormActions(
                Submit('submit', 'Analyze SEO', css_class='btn btn-primary'),
            )
        )