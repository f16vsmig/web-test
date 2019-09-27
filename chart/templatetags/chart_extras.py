from django import template
# from buildinginfo.models import Ismart, Weather

register = template.Library()


@register.filter(name='fields')
def field_label_list(model):
    objects = model._meta.get_fields()
    result = []
    for obj in objects:
        field_name = str(obj).split('.')
        result.append(field_name[2])
    return result[3:]

@register.filter(name='class_name')
def to_class_name(obj):
    return obj.__class__.__name__