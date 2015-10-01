from __future__ import unicode_literals

from django.utils import six

from tagulous.models.fields import SingleTagField, TagField


#
# Functions to load initial tags
# Used by tests and the management command `initialtags`
#

def field_initialise_tags(model, field, report=None):
    """
    Load any initial tags for the specified tag field
    
    You will not normally need to call this directly - instead use the
    management command ``initialtags``.
    
    Arguments:
        model       Model containing the field
        field       Field with initial tags to load
        report      Optional: a file handle to write verbose reports to
    
    Returns True if loaded, False if nothing to load
    """
    if not field.tag_options.initial:
        return False
        
    if report:
        report.write("Loading initial tags for %s.%s.%s\n" % (
            model._meta.app_label,
            model.__name__,
            field.name,
        ))
    
    descriptor = getattr(model, field.name)
    descriptor.load_initial()
    return True


def model_initialise_tags(model, report=None):
    """
    Load any initial tags for the given model
    
    You will not normally need to call this directly - instead use the
    management command ``initialtags``.
    
    Arguments:
        model       Model to check for tag fields to load
        report      Optional: a file handle to write verbose reports to
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

