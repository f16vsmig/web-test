from django import template

register = template.Library()


@register.filter(name='count')
def comment_objects_count(value, pk):
    return value.filter(board=pk).count()

@register.filter(name='subcount')
def subcomment_objects_count(value, pk):
    return value.filter(comment__board=pk).count()

@register.filter(name='sub')
def subtract(value, arg):
    return int(value) - int(arg)
