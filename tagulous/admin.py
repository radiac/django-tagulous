from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.shortcuts import render
from django.http import HttpResponseRedirect

from tagulous import models as tag_models
from tagulous import forms as tag_forms


###############################################################################
########################################################### Admin registration
###############################################################################

# Give contrib.admin a default widget for tag fields
admin.options.FORMFIELD_FOR_DBFIELD_DEFAULTS.update({
    tag_models.SingleTagField:  {'widget': tag_forms.AdminTagWidget},
    tag_models.TagField:        {'widget': tag_forms.AdminTagWidget},
})


class TaggedModelAdmin(admin.ModelAdmin):
    """
    Tag-aware abstract base class for ModelAdmin
    """
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(TaggedModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if (
            isinstance(db_field, (tag_models.SingleTagField, tag_models.TagField))
            and
            isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper)
            and
            isinstance(formfield.widget.widget, tag_forms.AdminTagWidget)
        ):
            formfield.widget = formfield.widget.widget
        return formfield


def _create_display(field):
    """
    ModelAdmin display function factory
    """
    def display(self, obj):
        return getattr(obj, field).get_tag_string()
    display.short_description = field.replace('_', ' ')
    return display


def enhance(model, admin_class):
    """
    Add tag support to the admin class based on the specified model
    """
    #
    # Get a list of all tag fields
    #
    
    # Dict of single tag fields, {name: tag}
    single_tag_fields = {}
    
    # Dict of normal tag fields, {name: tag}
    tag_fields = {}
    
    # List of all single and normal tag fields
    tag_field_names = []
    
    # Check for SingleTagField related fields
    for field in tag_models.singletagfields_from_model(model):
        single_tag_fields[field.name] = field
        tag_field_names.append(field.name)
    
    # Check for TagField m2m fields
    for field in tag_models.tagfields_from_model(model):
        tag_fields[field.name] = field
        tag_field_names.append(field.name)

    
    #
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
        # Make sure we're working with a list
        if isinstance(admin_class.list_display, tuple):
            admin_class.list_display = list(admin_class.list_display)
        
        for i, field in enumerate(admin_class.list_display):
            # If the field's not a callable, and not in the admin class already
            if not callable(field) and not hasattr(admin_class, field):
                # Only TagFields (admin can already handle SingleTagField FKs)
                if field in tag_fields:
                    # Create new field name and replace in list_display
                    display_name = '_tagulous_display_%s' % field
                    admin_class.list_display[i] = display_name
                
                    # Add display function to admin class
                    setattr(admin_class, display_name, _create_display(field))
    

def register(model, admin_class=None, site=None, **options):
    """
    Provide tag support to the model when it is registered with the admin site.
    
    For tagged models (have one or more SingleTagField or TagField fields):
        * Admin will support TagField in list_display
    
    For tag models (subclass of TagModel):
        * Admin will provide a merge action to merge tags
    
    For other models:
        * No changes made
    
    Arguments:
        model       Model to register
        admin_class Admin class for model
        site        Admin site to register with
                    Default: django.contrib.admin.site
        **options   Extra options for admin class
    
    This only supports one model, but is otherwise safe to use with non-tagged
    models.
    """
    # Look at the model we've been given
    if isinstance(model, tag_models.BaseTagDescriptor):
        # It's a tag descriptor; change it for the tag model itself
        model = model.tag_model
    
    elif not isinstance(model, ModelBase):
        raise ImproperlyConfigured(
            'Tagulous can only register a single model with admin.'
        )
    
    # Ensure we have a valid admin site
    if site is None:
        site = admin.site
    
    #
    # Determine appropriate admin class
    #
    if not admin_class:
        admin_class = admin.ModelAdmin
    
    # Going to make a list of base classes to inject
    cls_bases = []
    
    # If it's a tag model, subclass TagModelAdmin or TagTreeModelAdmin
    if issubclass(model, tag_models.BaseTagModel):
        if issubclass(model, tag_models.TagTreeModel):
            if not issubclass(admin_class, TagTreeModelAdmin):
                cls_bases += [TagTreeModelAdmin]
        else:
            if not issubclass(admin_class, TagModelAdmin):
                cls_bases += [TagModelAdmin]
    
    # If it's a tagged model, subclass TaggedModelAdmin
    singletagfields = tag_models.singletagfields_from_model(model)
    tagfields = tag_models.tagfields_from_model(model)
    if singletagfields or tagfields:
        if not issubclass(admin_class, TaggedModelAdmin):
            cls_bases += [TaggedModelAdmin]
    
    # If options specified, or other bases, will need to subclass admin_class
    if options or cls_bases:
        cls_bases += [admin_class]
        # Update options with anything the new subclasses could have overidden
        # in a custom ModelAdmin - unless they're already overridden in options
        options['__module__'] = __name__
        if admin_class != admin.ModelAdmin:
            options.update(dict(
                (k, v) for k, v in admin_class.__dict__.items()
                if k in ['list_display', 'list_filter', 'exclude', 'actions']
                and k not in options
            ))
        admin_class = type("%sAdmin" % model.__name__, tuple(cls_bases), options)
    
    # Enhance the model admin class
    enhance(model, admin_class)
    
    # Register the model
    # Don't pass options - we've already dealt with that
    site.register(model, admin_class)
    

###############################################################################
######################################################## Tag model admin tools
###############################################################################

class TagModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'count', 'protected']
    list_filter = ['protected']
    exclude = ['count']
    actions = ['merge_tags']
    
    def merge_tags(self, request, queryset):
        """
        Admin action to merge tags
        """
        # Thanks to:
        #   http://www.hoboes.com/Mimsy/hacks/django-actions-their-own-intermediate-page/
        
        # Create a form
        class MergeForm(forms.Form):
            # Keep selected items in same field, admin.ACTION_CHECKBOX_NAME
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            # Allow use to select from selected items
            merge_to = forms.ModelChoiceField(queryset)
        
        if 'merge' in request.POST:
            merge_form = MergeForm(request.POST)
            if merge_form.is_valid():
                merge_to = merge_form.cleaned_data['merge_to']
                merge_to.merge_tags(queryset)
                # ++ Can add level=messages.SUCCESS when django 1.4 is dropped
                self.message_user(request, 'Tags merged')
                return HttpResponseRedirect(request.get_full_path())
                
        else:
            tag_pks = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            if len(tag_pks) < 2:
                # ++ Can add level=messages.INFO when django 1.4 is dropped
                self.message_user(
                    request, 'You must select at least two tags to merge',
                )
                return HttpResponseRedirect(request.get_full_path())
            
            merge_form = MergeForm(
                initial={
                    admin.ACTION_CHECKBOX_NAME: request.POST.getlist(
                        admin.ACTION_CHECKBOX_NAME
                    )
                }
            )
            
        return render(request, 'tagulous/admin/merge_tags.html', {
            'title': 'Merge tags',
            'opts': self.model._meta,
            'merge_form': merge_form,
            'tags': queryset,
        })
    merge_tags.short_description = 'Merge selected tags...'

class TagTreeModelAdmin(TagModelAdmin):
    exclude = ['count', 'path']


def tag_model(model, site=None):
    "Deprecated - use register() instead"
    # ++ Remove in next release
    import warnings
    warnings.warn(
        'tag_model deprecated, use register instead', DeprecationWarning,
    )
    register(model, site=site)
