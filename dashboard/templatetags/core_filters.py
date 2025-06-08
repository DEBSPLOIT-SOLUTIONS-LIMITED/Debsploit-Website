# templatetags/core_filters.py
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.template.defaultfilters import floatformat
import re

register = template.Library()

@register.filter
def filter_by_slug(queryset, slug):
    """Filter queryset by slug"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(slug=slug)
    return queryset

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def currency(value):
    """Format currency with commas and dollar sign"""
    try:
        if value is None or value == '':
            return '$0'
        return f"${float(value):,.2f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return '$0'

@register.filter
def truncate_chars(value, arg):
    """Truncate string to specified number of characters"""
    try:
        limit = int(arg)
        if len(str(value)) > limit:
            return str(value)[:limit] + '...'
        return str(value)
    except (ValueError, TypeError):
        return str(value)

@register.filter
def add_class(field, css_class):
    """Add CSS class to form field"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field

@register.filter
def placeholder(field, text):
    """Add placeholder to form field"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'placeholder': text})
    return field

@register.filter
def stars_range(rating):
    """Generate range for star rating display"""
    try:
        rating = int(float(rating))
        return range(1, 6)  # 1 to 5 stars
    except (ValueError, TypeError):
        return range(1, 6)

@register.filter
def filled_stars(rating):
    """Get number of filled stars"""
    try:
        return int(float(rating))
    except (ValueError, TypeError):
        return 0

@register.filter
def empty_stars(rating):
    """Get number of empty stars"""
    try:
        filled = int(float(rating))
        return 5 - filled
    except (ValueError, TypeError):
        return 5

@register.filter
def split_by(value, delimiter):
    """Split string by delimiter"""
    if value:
        return str(value).split(delimiter)
    return []

@register.filter
def join_by(value, delimiter):
    """Join list by delimiter"""
    if value and hasattr(value, '__iter__'):
        return delimiter.join(str(item) for item in value)
    return str(value)

@register.filter
def slugify_custom(value):
    """Custom slugify filter"""
    import re
    from django.utils.text import slugify
    return slugify(value)

@register.filter
def time_ago(value):
    """Calculate time ago from datetime"""
    from django.utils import timezone
    from datetime import timedelta
    
    if not value:
        return ''
    
    now = timezone.now()
    if hasattr(value, 'replace'):
        if value.tzinfo is None:
            value = timezone.make_aware(value)
    
    diff = now - value
    
    if diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

@register.filter
def reading_time(content):
    """Calculate estimated reading time"""
    if not content:
        return "1 min read"
    
    # Strip HTML tags
    import re
    clean_text = re.sub(r'<[^>]+>', '', str(content))
    word_count = len(clean_text.split())
    
    # Average reading speed: 200 words per minute
    minutes = max(1, round(word_count / 200))
    return f"{minutes} min read"

@register.filter
def first_paragraph(content):
    """Extract first paragraph from content"""
    if not content:
        return ''
    
    import re
    # Split by paragraph tags or double newlines
    paragraphs = re.split(r'</?p[^>]*>|\n\n', str(content))
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph and len(paragraph) > 20:
            # Remove any remaining HTML tags
            clean_paragraph = re.sub(r'<[^>]+>', '', paragraph)
            return clean_paragraph[:200] + ('...' if len(clean_paragraph) > 200 else '')
    
    return str(content)[:200] + ('...' if len(str(content)) > 200 else '')

@register.filter
def highlight_search(text, search_term):
    """Highlight search term in text"""
    if not search_term or not text:
        return text
    
    import re
    highlighted = re.sub(
        f'({re.escape(search_term)})',
        r'<mark class="search-highlight">\1</mark>',
        str(text),
        flags=re.IGNORECASE
    )
    return mark_safe(highlighted)

@register.filter
def format_phone(phone):
    """Format phone number"""
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(phone))
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return str(phone)

@register.filter
def social_icon(platform):
    """Get social media icon class"""
    icons = {
        'facebook': 'fab fa-facebook-f',
        'twitter': 'fab fa-twitter',
        'instagram': 'fab fa-instagram',
        'linkedin': 'fab fa-linkedin-in',
        'youtube': 'fab fa-youtube',
        'github': 'fab fa-github',
        'tiktok': 'fab fa-tiktok',
        'pinterest': 'fab fa-pinterest',
        'snapchat': 'fab fa-snapchat',
        'whatsapp': 'fab fa-whatsapp',
        'telegram': 'fab fa-telegram',
        'discord': 'fab fa-discord',
    }
    return icons.get(platform.lower(), 'fas fa-link')

@register.filter
def file_size(bytes_value):
    """Convert bytes to human readable format"""
    try:
        bytes_value = float(bytes_value)
        if bytes_value < 1024:
            return f"{bytes_value:.0f} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
    except (ValueError, TypeError):
        return "0 B"

@register.filter
def badge_color(value):
    """Get badge color based on value"""
    colors = {
        'beginner': 'success',
        'intermediate': 'warning', 
        'advanced': 'danger',
        'expert': 'dark',
        'active': 'success',
        'inactive': 'secondary',
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'published': 'success',
        'draft': 'secondary',
        'featured': 'primary',
        'new': 'info',
        'popular': 'warning',
        'trending': 'danger',
    }
    return colors.get(str(value).lower(), 'primary')

@register.filter
def progress_percentage(current, total):
    """Calculate progress percentage"""
    try:
        if float(total) == 0:
            return 0
        percentage = (float(current) / float(total)) * 100
        return min(100, max(0, round(percentage)))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def difficulty_icon(difficulty):
    """Get difficulty level icon"""
    icons = {
        'beginner': 'fas fa-seedling',
        'intermediate': 'fas fa-chart-line',
        'advanced': 'fas fa-rocket',
        'expert': 'fas fa-crown',
    }
    return icons.get(str(difficulty).lower(), 'fas fa-star')

@register.filter
def service_type_icon(service_type):
    """Get service type icon"""
    icons = {
        'course': 'fas fa-graduation-cap',
        'workshop': 'fas fa-tools',
        'consultation': 'fas fa-comments',
        'development': 'fas fa-code',
        'design': 'fas fa-paint-brush',
        'marketing': 'fas fa-bullhorn',
        'training': 'fas fa-chalkboard-teacher',
        'mentoring': 'fas fa-user-tie',
        'project': 'fas fa-project-diagram',
        'support': 'fas fa-life-ring',
    }
    return icons.get(str(service_type).lower(), 'fas fa-cogs')

@register.simple_tag
def url_replace(request, **kwargs):
    """Replace URL parameters while preserving others"""
    updated = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, 0)
    return updated.urlencode()

@register.simple_tag
def current_url_with_params(request, **kwargs):
    """Get current URL with additional parameters"""
    from django.http import QueryDict
    params = QueryDict(mutable=True)
    params.update(request.GET)
    
    for key, value in kwargs.items():
        if value is not None:
            params[key] = value
        elif key in params:
            del params[key]
    
    return f"{request.path}?{params.urlencode()}" if params else request.path

@register.inclusion_tag('core/includes/pagination.html', takes_context=True)
def render_pagination(context, page_obj, paginator):
    """Render pagination component"""
    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'request': context['request'],
    }

@register.inclusion_tag('core/includes/breadcrumb.html', takes_context=True)
def render_breadcrumb(context, *args):
    """Render breadcrumb navigation"""
    breadcrumbs = []
    for i in range(0, len(args), 2):
        if i + 1 < len(args):
            breadcrumbs.append({
                'title': args[i],
                'url': args[i + 1] if args[i + 1] != '#' else None
            })
    
    return {
        'breadcrumbs': breadcrumbs,
        'request': context['request'],
    }