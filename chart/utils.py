    
def field_label_list(model):
    objects = model._meta.get_fields()
    result = []
    for i in objects:
        field_name = str(i).split('.')
        result.append(field_name[2])
    return result