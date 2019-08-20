from django import template

register = template.Library()

@register.filter(name='sub')
def subtract(value, arg):
    return int(value) - int(arg)

@register.filter(name='count')
def value_count(value, pk):
    return value.filter(pk=pk).count()