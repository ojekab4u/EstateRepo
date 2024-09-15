from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

from django import template
from django.utils.html import mark_safe

register = template.Library()

@register.filter
def currency(value):
    if not value:
        return ''
    try:
        value = float(value)
        return mark_safe(f'₦{value:,.2f}')
    except ValueError:
        return ''