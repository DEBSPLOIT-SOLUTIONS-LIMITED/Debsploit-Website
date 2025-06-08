from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import FormActions

from .models import (
    Service, ServiceCategory, Course, Enrollment, Task, TaskApplication,
    TaskSubmission, ServiceReview
)

class ServiceForm(forms.ModelForm):
    """Form for creating/editing services"""
    
    class Meta:
        model = Service
        fields = [
            'title', 'slug', 'category', 'description', 'detailed_description',
            'service_type', 'difficulty_level', 'price', 'discount_price',
            'duration_weeks', 'max_participants', 'featured_image',
            'video_url', 'prerequisites', 'required_tools', 'is_active',
            'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'prerequisites': forms.Textarea(attrs={'rows': 3}),
            'required_tools': forms.Textarea(attrs={'rows': 3}),
            'video_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('title', css_class='form-group col-md-8 mb-0'),
                    Column('slug', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('category', css_class='form-group col-md-6 mb-0'),
                    Column('service_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'description',
                'detailed_description',
            ),
            Fieldset(
                'Pricing & Details',
                Row(
                    Column('price', css_class='form-group col-md-4 mb-0'),
                    Column('discount_price', css_class='form-group col-md-4 mb-0'),
                    Column('difficulty_level', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('duration_weeks', css_class='form-group col-md-6 mb-0'),
                    Column('max_participants', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Media & Requirements',
                'featured_image',
                'video_url',
                'prerequisites',
                'required_tools',
            ),
            Fieldset(
                'Settings',
                Row(
                    Column('is_active', css_class='form-group col-md-6 mb-0'),
                    Column('is_featured', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            FormActions(
                Submit('submit', 'Save Service', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "services:service_list" %}" class="btn btn-secondary btn-lg ms-2">Cancel</a>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        
        if discount_price and price and discount_price >= price:
            raise ValidationError('Discount price must be less than regular price.')
        
        return cleaned_data

class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    
    class Meta:
        model = Course
        fields = [
            'service', 'instructor', 'start_date', 'end_date', 'schedule',
            'location', 'meeting_link', 'syllabus', 'resources',
            'is_enrollment_open'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'schedule': forms.Textarea(attrs={'rows': 3}),
            'meeting_link': forms.URLInput(attrs={'placeholder': 'https://zoom.us/j/...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                'Course Details',
                Row(
                    Column('service', css_class='form-group col-md-6 mb-0'),
                    Column('instructor', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('start_date', css_class='form-group col-md-6 mb-0'),
                    Column('end_date', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'schedule',
            ),
            Fieldset(
                'Location & Resources',
                Row(
                    Column('location', css_class='form-group col-md-6 mb-0'),
                    Column('meeting_link', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'syllabus',
                'resources',
            ),
            Fieldset(
                'Settings',
                'is_enrollment_open',
            ),
            FormActions(
                Submit('submit', 'Save Course', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "services:course_list" %}" class="btn btn-secondary btn-lg ms-2">Cancel</a>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError('End date must be after start date.')
        
        return cleaned_data

class EnrollmentForm(forms.ModelForm):
    """Form for manual enrollment"""
    
    class Meta:
        model = Enrollment
        fields = ['user', 'course', 'status', 'payment_status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Row(
                Column('user', css_class='form-group col-md-6 mb-0'),
                Column('course', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-6 mb-0'),
                Column('payment_status', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Create Enrollment', css_class='btn btn-primary'),
            )
        )

class TaskForm(forms.ModelForm):
    """Form for creating/editing tasks"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'priority', 'status',
            'estimated_hours', 'due_date', 'requirements', 'deliverables',
            'budget', 'points_reward', 'attachment'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'requirements': forms.Textarea(attrs={'rows': 3}),
            'deliverables': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                'Task Information',
                'title',
                'description',
                Row(
                    Column('task_type', css_class='form-group col-md-4 mb-0'),
                    Column('priority', css_class='form-group col-md-4 mb-0'),
                    Column('status', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Timeline & Budget',
                Row(
                    Column('estimated_hours', css_class='form-group col-md-4 mb-0'),
                    Column('budget', css_class='form-group col-md-4 mb-0'),
                    Column('points_reward', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                'due_date',
            ),
            Fieldset(
                'Requirements',
                'requirements',
                'deliverables',
                'attachment',
            ),
            FormActions(
                Submit('submit', 'Save Task', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "services:task_list" %}" class="btn btn-secondary btn-lg ms-2">Cancel</a>')
            )
        )

class TaskApplicationForm(forms.ModelForm):
    """Form for applying to tasks"""
    
    class Meta:
        model = TaskApplication
        fields = ['cover_letter', 'proposed_timeline', 'proposed_budget']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Explain why you are the perfect fit for this task. Include your relevant experience and approach.'
            }),
            'proposed_timeline': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe your proposed timeline for completing this task.'
            }),
            'proposed_budget': forms.NumberInput(attrs={
                'placeholder': 'Your proposed budget (optional)',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info"><i class="fas fa-info-circle me-2"></i>Make your application stand out by providing detailed information about your experience and approach.</div>'),
            'cover_letter',
            'proposed_timeline',
            'proposed_budget',
            FormActions(
                Submit('submit', 'Submit Application', css_class='btn btn-primary btn-lg'),
                HTML('<a href="javascript:history.back()" class="btn btn-secondary btn-lg ms-2">Back</a>')
            )
        )

class TaskSubmissionForm(forms.ModelForm):
    """Form for submitting completed tasks"""
    
    class Meta:
        model = TaskSubmission
        fields = ['description', 'files', 'github_link', 'demo_link']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Describe what you have accomplished and how you approached the task.'
            }),
            'github_link': forms.URLInput(attrs={'placeholder': 'https://github.com/...'}),
            'demo_link': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            HTML('<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>Provide a comprehensive submission with all relevant files and links.</div>'),
            'description',
            'files',
            Row(
                Column('github_link', css_class='form-group col-md-6 mb-0'),
                Column('demo_link', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Submit Work', css_class='btn btn-success btn-lg'),
                HTML('<a href="javascript:history.back()" class="btn btn-secondary btn-lg ms-2">Back</a>')
            )
        )

class ServiceReviewForm(forms.ModelForm):
    """Form for reviewing services"""
    
    class Meta:
        model = ServiceReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=ServiceReview.RATING_CHOICES, attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'placeholder': 'Brief title for your review',
                'class': 'form-control'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your experience with this service...',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info"><i class="fas fa-star me-2"></i>Your review helps other students make informed decisions.</div>'),
            'rating',
            'title',
            'comment',
            FormActions(
                Submit('submit', 'Submit Review', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancel</button>')
            )
        )

class ServiceSearchForm(forms.Form):
    """Form for searching services"""
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search services...',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    service_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Service.SERVICE_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    difficulty_level = forms.ChoiceField(
        choices=[('', 'All Levels')] + list(Service.DIFFICULTY_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('price', 'Price: Low to High'),
            ('-price', 'Price: High to Low'),
            ('title', 'Name: A to Z'),
            ('-title', 'Name: Z to A'),
            ('-average_rating', 'Highest Rated'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='col-md-3'),
                Column('category', css_class='col-md-2'),
                Column('service_type', css_class='col-md-2'),
                Column('difficulty_level', css_class='col-md-2'),
                Column('min_price', css_class='col-md-1'),
                Column('max_price', css_class='col-md-1'),
                Column('sort', css_class='col-md-1'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Search', css_class='btn btn-primary'),
                HTML('<a href="?" class="btn btn-secondary ms-2">Clear</a>')
            )
        )

class TaskSearchForm(forms.Form):
    """Form for searching tasks"""
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search tasks...',
            'class': 'form-control'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Task.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    task_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Task.TASK_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + list(Task.PRIORITY_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Budget',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    max_budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Budget',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('budget', 'Budget: Low to High'),
            ('-budget', 'Budget: High to Low'),
            ('due_date', 'Due Date: Earliest'),
            ('-due_date', 'Due Date: Latest'),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='col-md-3'),
                Column('status', css_class='col-md-2'),
                Column('task_type', css_class='col-md-2'),
                Column('priority', css_class='col-md-1'),
                Column('min_budget', css_class='col-md-1'),
                Column('max_budget', css_class='col-md-1'),
                Column('sort', css_class='col-md-2'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Search', css_class='btn btn-primary'),
                HTML('<a href="?" class="btn btn-secondary ms-2">Clear</a>')
            )
        )

class ServiceCategoryForm(forms.ModelForm):
    """Form for creating/editing service categories"""
    
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description', 'icon', 'color', 'is_active', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={
                'placeholder': 'e.g., fas fa-code',
                'help_text': 'Font Awesome icon class'
            }),
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
                Column('name', css_class='form-group col-md-8 mb-0'),
                Column('order', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('icon', css_class='form-group col-md-8 mb-0'),
                Column('color', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'is_active',
            FormActions(
                Submit('submit', 'Save Category', css_class='btn btn-primary'),
            )
        )

class BulkEnrollmentForm(forms.Form):
    """Form for bulk enrolling users"""
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_enrollment_open=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    users = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Enter email addresses, one per line',
            'class': 'form-control'
        }),
        help_text="Enter one email address per line"
    )
    send_notification = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Send enrollment confirmation emails"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            'course',
            'users',
            'send_notification',
            FormActions(
                Submit('submit', 'Enroll Users', css_class='btn btn-primary'),
            )
        )
    
    def clean_users(self):
        users_text = self.cleaned_data.get('users')
        if not users_text:
            raise ValidationError('Please enter at least one email address.')
        
        emails = [email.strip() for email in users_text.split('\n') if email.strip()]
        
        if not emails:
            raise ValidationError('Please enter valid email addresses.')
        
        # Validate email format
        from django.core.validators import validate_email
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError(f'Invalid email address: {email}')
        
        return emails

class TaskFilterForm(forms.Form):
    """Form for filtering tasks in admin"""
    assigned_to = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="All Developers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Task.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + list(Task.PRIORITY_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    overdue_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set queryset for assigned_to field
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(
            user_type='developer',
            is_active=True
        )
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('assigned_to', css_class='col-md-3'),
                Column('status', css_class='col-md-3'),
                Column('priority', css_class='col-md-3'),
                Column('overdue_only', css_class='col-md-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Filter', css_class='btn btn-primary'),
                HTML('<a href="?" class="btn btn-secondary ms-2">Clear</a>')
            )
        )