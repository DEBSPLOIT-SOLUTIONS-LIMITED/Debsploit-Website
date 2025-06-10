# File: services/templatetags/service_filters.py

from django import template
from decimal import Decimal, InvalidOperation
import re

register = template.Library()

@register.filter
def currency(value):
    """Format a number as KSH currency."""
    if value is None or value == '':
        return "KSH 0.00"
    
    try:
        # Convert to Decimal for precise calculation
        amount = Decimal(str(value))
        # Format with commas for thousands separator
        formatted = f"{amount:,.2f}"
        return f"KSH {formatted}"
    except (ValueError, TypeError, InvalidOperation):
        return "KSH 0.00"

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    if value is None or arg is None:
        return 0
    
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def badge_color(difficulty_level):
    """Return appropriate badge color for difficulty level."""
    if not difficulty_level:
        return 'secondary'
    
    colors = {
        'beginner': 'success',
        'intermediate': 'warning', 
        'advanced': 'danger'
    }
    return colors.get(difficulty_level.lower(), 'secondary')

@register.filter
def percentage(value, total):
    """Calculate percentage of value from total."""
    if not value or not total:
        return 0
    
    try:
        total_num = int(total)
        if total_num == 0:
            return 0
        return round((int(value) / total_num) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by arg."""
    if value is None or arg is None:
        return 0
    
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def format_duration(weeks):
    """Format duration in weeks to a readable string."""
    if not weeks:
        return "Self-paced"
    
    try:
        weeks_num = int(weeks)
        if weeks_num == 1:
            return "1 week"
        elif weeks_num < 4:
            return f"{weeks_num} weeks"
        elif weeks_num < 52:
            months = round(weeks_num / 4.33)
            return f"{months} month{'s' if months != 1 else ''}"
        else:
            years = round(weeks_num / 52)
            return f"{years} year{'s' if years != 1 else ''}"
    except (ValueError, TypeError):
        return "Self-paced"