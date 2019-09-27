    
def field_label_list(model):
    objects = model._meta.get_fields()
    result = []
    for obj in objects:
        field_name = str(obj).split('.')
        result.append(field_name[2])
        # field_name = str(obj).split('.')
        # result.append(field_name)
    return result