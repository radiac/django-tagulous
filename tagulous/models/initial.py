from tagulous.models.fields import SingleTagField, TagField


#
# Functions to load initial tags
# Used by tests and the management command `initialtags`
#

def field_initialise_tags(model, field, report=False):
    """
    Load any initial tags for the specified tag field
    Returns True if loaded, False if nothing to load
    If report=True, a line is written to STDOUT to report the field is loading
    """
    if not field.tag_options.initial:
        return False
        
    if report:
        print "Loading initial tags for %s.%s.%s" % (
            model._meta.app_label,
            model.__name__,
            field.name,
        )
    
    descriptor = getattr(model, field.name)
    descriptor.load_initial()
    return True


def model_initialise_tags(model, report=False):
    """
    Load any initial tags for the given model
    Do not call directly - instead use the management command `initialtags`
    Arguments:
        model       Model to check for tag fields to load
        report      Passed to field_initialise_tags
    """
    if hasattr(model._meta, 'get_fields'):
        # Django 1.8 uses new meta API
        fields = model._meta.get_fields()
    else:
        fields = model._meta.fields + model._meta.many_to_many
        
    for field in fields:
        if isinstance(
            field,
            (SingleTagField, TagField)
        ):
            field_initialise_tags(model, field, report)

