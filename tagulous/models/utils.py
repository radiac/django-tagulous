"""
Model utils
"""

def singletagfields_from_model(model):
    """Get a list of SingleTagField fields from a model class"""
    return [
        field in model._meta.fields
        if isinstance(field, tag_models.SingleTagField)
    ]

def tagfields_from_model(model):
    """Get a list of TagField fields from a model class"""
    return [
        field in model._meta.many_to_many
        if isinstance(field, tag_models.TagField)
    ]
