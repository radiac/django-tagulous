from django.contrib import admin
from django.db.models.base import ModelBase
from django.db.models import FieldDoesNotExist

from tagulous import models, forms

    
def register(*args, **kwargs):
    """
    Add tag field support to the admin class, then register with
    django.contrib.admin.site
    
    This only supports one model
    """
    register_site(admin.site, *args, **kwargs)


def register_site(site, model, admin_class=None, **options):
    """
    Add tag field support to the admin class, then register with the specified
    admin site
    
    This only supports one model
    """
    if not isinstance(model, ModelBase):
        raise ImproperlyConfigured(
            'Tagulous can only register a single model with admin.'
        )
    
    #
    # Ensure we have an admin class
    # This duplicates functionality in site.register(), but is needed here
    # so we can customise it before we validate
    #
    if not admin_class:
        admin_class = admin.ModelAdmin
    if options:
        options['__module__'] = __name__
        admin_class = type("%sAdmin" % model.__name__, (admin_class,), options)
    
    
    #
    # Set up tag support
    #
    
    # Get a list of all tag fields
    single_tag_fields = {}
    tag_fields = {}
    tag_field_names = []
    
    # Check for SingleTagField related fields
    for field in model._meta.fields:
        if isinstance(field, models.SingleTagField):
            single_tag_fields[field.name] = field
            tag_field_names.append(field.name)
    
    # Check for TagField m2m fields
    for field in model._meta.many_to_many:
        if isinstance(field, models.TagField):
            tag_fields[field.name] = field
            tag_field_names.append(field.name)
    
    
    # Ensure any tag fields in list_display are rendered by functions
    #
    # The admin.site.register will complain if it's a ManyToManyField, so this
    # will work around that.
    #
    # We also need to have a different name to the model field, otherwise the
    # ChangeList class will just use the model field - that would get the tag
    # strings showing in the table, but the column would be sortable which
    # would cause problems for TagFields, and the display function would never
    # get called, which would be unexpected for anyone maintaining this code.
    if hasattr(admin_class, 'list_display'):
        for i, field in enumerate(admin_class.list_display):
            # If the field's not a callable, and not in the admin class already
            if not callable(field) and not hasattr(admin_class, field):
                # Check to see if it's a SingleTagField or a TagField
                if field in tag_field_names:
                    # Create new field name and replace in list_display
                    display_name = '_tagulous_display_%s' % field
                    admin_class.list_display[i] = display_name
                    
                    # Add display function to admin class
                    setattr(admin_class, display_name, create_display(field))
    
    
    # Ensure every tag field uses the correct widget
#    print hasattr(admin_class, 'formfield_overrides')
    admin_class.formfield_overrides = {
        models.SingleTagField: {'widget': forms.AdminTagWidget},
        models.TagField: {'widget': forms.AdminTagWidget},
    }
    
    site.register(model, admin_class)
    
    
def create_display(field):
    def display(self, obj):
        return 'xx' +  getattr(obj, field).get_tag_string()
    display.short_description = field.replace('_', ' ')
    return display
