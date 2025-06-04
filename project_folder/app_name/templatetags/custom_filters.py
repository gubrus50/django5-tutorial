from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """Replace characters in a string. Usage: {{ string|replace:'_|-' }}"""
    old, new = arg.split('|')
    return value.replace(old, new)