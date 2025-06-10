# Create this file: services/templatetags/service_filters.py

import decimal
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return 0

@register.filter
def currency(value):
    """Format a number as currency."""
    try:
        return f"KES {Decimal(str(value)):,.2f}"
    except (ValueError, TypeError):
        return "KES 0.00"

@register.filter
def badge_color(difficulty_level):
    """Return appropriate badge color for difficulty level."""
    colors = {
        'beginner': 'success',
        'intermediate': 'warning', 
        'advanced': 'danger'
    }
    return colors.get(difficulty_level, 'secondary')

@register.filter
def percentage(value, total):
    """Calculate percentage of value from total."""
    try:
        if int(total) == 0:
            return 0
        return round((int(value) / int(total)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0