from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_countries.widgets import CountrySelectWidget
from phonenumber_field.formfields import PhoneNumberField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import FormActions, Tab, TabHolder

from accounts.models import UserSkill
from services.models import TaskApplication, TaskSubmission
from .models import ProjectPortfolio, DeveloperProfile

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    phone = PhoneNumberField(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'bio',
            'profile_picture', 'date_of_birth', 'country', 'city', 'address',
            'company', 'job_title', 'experience_years', 'skill_level',
            'linkedin_url', 'github_url', 'portfolio_url'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'country': CountrySelectWidget(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Fix country field
        self.fields['country'].empty_label = "(Select Country)"
        self.fields['country'].required = False
        
        # Fix phone field
        self.fields['phone'].widget.attrs.update({'class': 'form-control'})
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    'Personal Information',
                    Row(
                        Column('first_name', css_class='form-group col-md-6 mb-0'),
                        Column('last_name', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('email', css_class='form-group col-md-8 mb-0'),
                        Column('phone', css_class='form-group col-md-4 mb-0'),
                        css_class='form-row'
                    ),
                    'bio',
                    'profile_picture',
                    'date_of_birth',
                ),
                Tab(
                    'Location',
                    Row(
                        Column('country', css_class='form-group col-md-6 mb-0'),
                        Column('city', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    'address',
                ),
                Tab(
                    'Professional',
                    Row(
                        Column('company', css_class='form-group col-md-6 mb-0'),
                        Column('job_title', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    Row(
                        Column('experience_years', css_class='form-group col-md-6 mb-0'),
                        Column('skill_level', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
                    'linkedin_url',
                    'github_url',
                    'portfolio_url',
                )
            ),
            FormActions(
                Submit('submit', 'Update Profile', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "dashboard:home" %}" class="btn btn-secondary btn-lg ms-2">Cancel</a>')
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use.")
        return email

class DeveloperProfileForm(forms.ModelForm):
    class Meta:
        model = DeveloperProfile
        fields = [
            'hourly_rate', 'availability', 'preferred_project_types',
            'years_of_experience', 'portfolio_website', 'behance_url',
            'dribbble_url', 'is_accepting_projects', 'next_available_date'
        ]
        widgets = {
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'availability': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'next_available_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'preferred_project_types': forms.CheckboxSelectMultiple(),
            'portfolio_website': forms.URLInput(attrs={'class': 'form-control'}),
            'behance_url': forms.URLInput(attrs={'class': 'form-control'}),
            'dribbble_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_accepting_projects': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Professional Details',
                Row(
                    Column('hourly_rate', css_class='form-group col-md-6 mb-0'),
                    Column('availability', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'years_of_experience',
                'preferred_project_types',
            ),
            Fieldset(
                'Portfolio Links',
                'portfolio_website',
                'behance_url',
                'dribbble_url',
            ),
            Fieldset(
                'Availability',
                Row(
                    Column('is_accepting_projects', css_class='form-group col-md-6 mb-0'),
                    Column('next_available_date', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            FormActions(
                Submit('submit', 'Update Developer Profile', css_class='btn btn-success btn-lg')
            )
        )

class UserSkillForm(forms.ModelForm):
    class Meta:
        model = UserSkill
        fields = ['name', 'category', 'proficiency', 'years_experience']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Python, JavaScript, Adobe Photoshop'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'proficiency': forms.Select(attrs={'class': 'form-control'}),
            'years_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 50
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('proficiency', css_class='form-group col-md-6 mb-0'),
                Column('years_experience', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Add Skill', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancel</button>')
            )
        )
    
    def save(self, commit=True):
        skill = super().save(commit=False)
        if self.user:
            skill.user = self.user
        if commit:
            skill.save()
        return skill

class ProjectPortfolioForm(forms.ModelForm):
    class Meta:
        model = ProjectPortfolio
        fields = [
            'title', 'description', 'project_type', 'status',
            'github_url', 'live_demo_url', 'project_image', 'project_file',
            'technologies', 'start_date', 'end_date', 'is_public', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'project_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'live_demo_url': forms.URLInput(attrs={'class': 'form-control'}),
            'project_image': forms.FileInput(attrs={'class': 'form-control'}),
            'project_file': forms.FileInput(attrs={'class': 'form-control'}),
            'technologies': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Python, Django, React, PostgreSQL'
            }),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                'Project Information',
                'title',
                'description',
                Row(
                    Column('project_type', css_class='form-group col-md-6 mb-0'),
                    Column('status', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'technologies',
            ),
            Fieldset(
                'Links and Media',
                'github_url',
                'live_demo_url',
                'project_image',
                'project_file',
            ),
            Fieldset(
                'Timeline',
                Row(
                    Column('start_date', css_class='form-group col-md-6 mb-0'),
                    Column('end_date', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Visibility',
                Row(
                    Column('is_public', css_class='form-group col-md-6 mb-0'),
                    Column('is_featured', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            FormActions(
                Submit('submit', 'Save Project', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "dashboard:portfolio" %}" class="btn btn-secondary btn-lg ms-2">Cancel</a>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date cannot be before start date.")
        
        return cleaned_data
    
    def save(self, commit=True):
        project = super().save(commit=False)
        if self.user:
            project.user = self.user
        if commit:
            project.save()
        return project

class TaskApplicationForm(forms.ModelForm):
    class Meta:
        model = TaskApplication
        fields = ['cover_letter', 'proposed_timeline', 'proposed_budget']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Explain why you are the best fit for this task. Include your relevant experience and approach.'
            }),
            'proposed_timeline': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your proposed timeline for completing this task.'
            }),
            'proposed_budget': forms.NumberInput(attrs={
                'class': 'form-control',
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
    class Meta:
        model = TaskSubmission
        fields = ['description', 'files', 'github_link', 'demo_link']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Describe what you have accomplished and how you approached the task.'
            }),
            'files': forms.FileInput(attrs={'class': 'form-control'}),
            'github_link': forms.URLInput(attrs={'class': 'form-control'}),
            'demo_link': forms.URLInput(attrs={'class': 'form-control'}),
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

class ContactAdminForm(forms.Form):
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief subject of your message'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message to the admin team'
        })
    )
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Row(
                Column('subject', css_class='form-group col-md-8 mb-0'),
                Column('priority', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'message',
            FormActions(
                Submit('submit', 'Send Message', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancel</button>')
            )
        )

class BulkActionForm(forms.Form):
    """Form for bulk actions on various models"""
    ACTION_CHOICES = [
        ('', 'Select action...'),
        ('mark_read', 'Mark as Read'),
        ('mark_unread', 'Mark as Unread'),
        ('delete', 'Delete'),
        ('archive', 'Archive'),
    ]
    
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)
    selected_items = forms.CharField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        self.model_type = kwargs.pop('model_type', None)
        super().__init__(*args, **kwargs)
        
        # Customize actions based on model type
        if self.model_type == 'notifications':
            self.fields['action'].choices = [
                ('', 'Select action...'),
                ('mark_read', 'Mark as Read'),
                ('mark_unread', 'Mark as Unread'),
                ('delete', 'Delete'),
            ]
        elif self.model_type == 'tasks':
            self.fields['action'].choices = [
                ('', 'Select action...'),
                ('mark_complete', 'Mark as Complete'),
                ('archive', 'Archive'),
                ('assign_to_me', 'Assign to Me'),
            ]
        elif self.model_type == 'projects':
            self.fields['action'].choices = [
                ('', 'Select action...'),
                ('mark_featured', 'Mark as Featured'),
                ('unmark_featured', 'Remove from Featured'),
                ('make_public', 'Make Public'),
                ('make_private', 'Make Private'),
                ('delete', 'Delete'),
            ]