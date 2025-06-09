import re
import uuid
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from phonenumber_field.formfields import PhoneNumberField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import FormActions, Tab, TabHolder
from allauth.account.forms import SignupForm

from .models import UserSkill, UserNotification

User = get_user_model()

# Allauth Custom Signup Form
class CustomSignupForm(SignupForm):
    """Custom allauth signup form that includes user type selection"""
    
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name',
            'class': 'form-control'
        })
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Choose your primary role on the platform"
    )
    phone = PhoneNumberField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+254 700 000 000',
            'class': 'form-control'
        }),
        help_text="Optional. Include country code"
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the Terms of Service and Privacy Policy",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field attributes
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Email Address',
            'class': 'form-control'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Password',
            'class': 'form-control'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm Password',
            'class': 'form-control'
        })
        
        # Add help text
        self.fields['user_type'].help_text = 'Choose your primary role on the platform'
        self.fields['phone'].help_text = 'Optional. Include country code (e.g., +254 700 000 000)'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def generate_username(self, email, first_name, last_name):
        """Generate a unique username"""
        if email:
            # Extract base from email (part before @)
            base_username = re.sub(r'[^a-zA-Z0-9]', '', email.split('@')[0])
        elif first_name and last_name:
            # Use first and last name
            base_username = re.sub(r'[^a-zA-Z0-9]', '', f"{first_name}{last_name}")
        else:
            # Fallback to user + uuid
            base_username = f"user{str(uuid.uuid4())[:8]}"
        
        # Ensure it's not too long
        base_username = base_username[:20].lower()
        
        # Make it unique
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def save(self, request):
        """Save the user with the additional fields"""
        user = super().save(request)
        
        # Set additional fields
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        
        # Auto-generate username
        user.username = self.generate_username(
            self.cleaned_data['email'],
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name']
        )
        
        if self.cleaned_data.get('phone'):
            user.phone = self.cleaned_data['phone']
        
        user.save()
        return user

# Keep your existing CustomUserCreationForm for other uses
class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form (for non-allauth use)"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPES, required=True)
    phone = PhoneNumberField(required=False)
    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the Terms of Service and Privacy Policy"
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'user_type', 
                 'phone', 'password1', 'password2', 'terms_accepted')
        # Removed username from fields since we'll auto-generate it
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        # Remove username field from the form display
        if 'username' in self.fields:
            del self.fields['username']
        
        self.helper.layout = Layout(
            Fieldset(
                'Personal Information',
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('email', css_class='form-group col-md-8 mb-0'),
                    Column('user_type', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                'phone',
            ),
            Fieldset(
                'Security',
                'password1',
                'password2',
            ),
            Fieldset(
                'Terms & Conditions',
                'terms_accepted',
            ),
            FormActions(
                Submit('submit', 'Create Account', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "account_login" %}" class="btn btn-secondary btn-lg ms-2">Already have an account?</a>')
            )
        )
        
        # Add help text
        self.fields['user_type'].help_text = 'Choose your primary role on the platform.'
        self.fields['phone'].help_text = 'Optional. Include country code (e.g., +254 700 000 000)'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def generate_username(self, email, first_name, last_name):
        """Generate a unique username"""
        if email:
            # Extract base from email (part before @)
            base_username = re.sub(r'[^a-zA-Z0-9]', '', email.split('@')[0])
        elif first_name and last_name:
            # Use first and last name
            base_username = re.sub(r'[^a-zA-Z0-9]', '', f"{first_name}{last_name}")
        else:
            # Fallback to user + uuid
            base_username = f"user{str(uuid.uuid4())[:8]}"
        
        # Ensure it's not too long
        base_username = base_username[:20].lower()
        
        # Make it unique
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        
        # Auto-generate username
        user.username = self.generate_username(
            self.cleaned_data['email'],
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name']
        )
        
        if self.cleaned_data['phone']:
            user.phone = self.cleaned_data['phone']
        
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Complete user profile form"""
    country = CountryField(blank_label='(select country)').formfield()
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
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'linkedin_url': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'github_url': forms.URLInput(attrs={'placeholder': 'https://github.com/yourusername'}),
            'portfolio_url': forms.URLInput(attrs={'placeholder': 'https://yourportfolio.com'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                    Row(
                        Column('profile_picture', css_class='form-group col-md-6 mb-0'),
                        Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                        css_class='form-row'
                    ),
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
                ),
                Tab(
                    'Online Presence',
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

class UserSkillForm(forms.ModelForm):
    """Form for adding/editing user skills"""
    
    class Meta:
        model = UserSkill
        fields = ['name', 'category', 'proficiency', 'years_experience']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Python, JavaScript, Adobe Photoshop',
                'class': 'form-control'
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
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('category', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('proficiency', css_class='form-group col-md-6 mb-3'),
                Column('years_experience', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Add Skill', css_class='btn btn-primary'),
                HTML('<button type="button" class="btn btn-secondary ms-2" data-bs-dismiss="modal">Cancel</button>')
            )
        )
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if self.user and UserSkill.objects.filter(
            user=self.user, 
            name__iexact=name
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError("You already have this skill in your profile.")
        return name
    
    def save(self, commit=True):
        skill = super().save(commit=False)
        if self.user:
            skill.user = self.user
        if commit:
            skill.save()
        return skill

class UserSearchForm(forms.Form):
    """Form for searching users"""
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, email, company...',
            'class': 'form-control'
        })
    )
    user_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(User.USER_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    verified = forms.ChoiceField(
        choices=[
            ('', 'All Users'),
            ('true', 'Verified Only'),
            ('false', 'Unverified Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Country',
            'class': 'form-control'
        })
    )
    sort = forms.ChoiceField(
        choices=[
            ('-date_joined', 'Newest First'),
            ('date_joined', 'Oldest First'),
            ('-points', 'Most Points'),
            ('points', 'Least Points'),
            ('first_name', 'Name A-Z'),
            ('-first_name', 'Name Z-A'),
        ],
        initial='-date_joined',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='col-md-4'),
                Column('user_type', css_class='col-md-2'),
                Column('verified', css_class='col-md-2'),
                Column('country', css_class='col-md-2'),
                Column('sort', css_class='col-md-2'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', 'Search', css_class='btn btn-primary'),
                HTML('<a href="?" class="btn btn-secondary ms-2">Clear</a>')
            )
        )

class ContactAdminForm(forms.Form):
    """Form for contacting admin"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Brief subject of your message',
            'class': 'form-control'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Your message to the admin team',
            'class': 'form-control'
        })
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
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

class PasswordChangeForm(forms.Form):
    """Custom password change form"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            'current_password',
            'new_password1',
            'new_password2',
            FormActions(
                Submit('submit', 'Change Password', css_class='btn btn-primary'),
            )
        )
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("New passwords don't match.")
        
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user

class NotificationPreferencesForm(forms.ModelForm):
    """Form for managing notification preferences"""
    email_notifications = forms.BooleanField(
        required=False,
        label="Email Notifications",
        help_text="Receive notifications via email"
    )
    task_notifications = forms.BooleanField(
        required=False,
        label="Task Updates",
        help_text="Get notified about task assignments and updates"
    )
    achievement_notifications = forms.BooleanField(
        required=False,
        label="Achievements",
        help_text="Get notified when you earn achievements"
    )
    course_notifications = forms.BooleanField(
        required=False,
        label="Course Updates",
        help_text="Receive updates about your enrolled courses"
    )
    marketing_notifications = forms.BooleanField(
        required=False,
        label="Marketing Emails",
        help_text="Receive newsletters and promotional content"
    )
    
    class Meta:
        model = User
        fields = []  # We'll handle preferences separately
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Notification Preferences',
                'email_notifications',
                'task_notifications',
                'achievement_notifications',
                'course_notifications',
                'marketing_notifications',
            ),
            FormActions(
                Submit('submit', 'Save Preferences', css_class='btn btn-primary'),
            )
        )

class AccountDeletionForm(forms.Form):
    """Form for account deletion confirmation"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm'
        }),
        help_text="Enter your password to confirm account deletion"
    )
    confirmation = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type "DELETE" to confirm'
        }),
        help_text="Type DELETE to confirm"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            HTML('<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i><strong>Warning:</strong> This action cannot be undone. All your data will be permanently deleted.</div>'),
            'password',
            'confirmation',
            FormActions(
                Submit('submit', 'Delete Account', css_class='btn btn-danger'),
                HTML('<a href="{% url "dashboard:profile" %}" class="btn btn-secondary ms-2">Cancel</a>')
            )
        )
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise ValidationError("Incorrect password.")
        return password
    
    def clean_confirmation(self):
        confirmation = self.cleaned_data.get('confirmation')
        if confirmation != 'DELETE':
            raise ValidationError("You must type 'DELETE' to confirm.")
        return confirmation