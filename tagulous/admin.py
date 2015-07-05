from django import forms
from django.contrib import admin
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
    

def register(model, admin_class=None, **options):
    """
    Add tag field support to the admin class, then register with the specified
    admin site
    
    Arguments:
        model       Model to register
        admin_class Admin class for model
        site        Admin site to register with
                    Default: django.contrib.admin.site
        **options   Extra options for admin class
    
    This only supports one model
    """
    if not isinstance(model, ModelBase):
        raise ImproperlyConfigured(
            'Tagulous can only register a single model with admin.'
        )
    
    # Get site from args
    site = options.pop('site', admin.site)
    
    #
    # Ensure we have an admin class
    # This is similar to functionality in site.register(), but it ensures that
    # the model class is a subclass of TaggedModelAdmin.
    #
    if not admin_class:
        admin_class = admin.ModelAdmin
    
    cls_bases = None
    if not issubclass(admin_class, TaggedModelAdmin):
        cls_bases = (TaggedModelAdmin, admin_class)
    elif options:
        cls_bases = (admin_class,)
        
    if cls_bases is not None:
        options['__module__'] = __name__
        admin_class = type("%sAdmin" % model.__name__, cls_bases, options)
    
    # Enhance the model class
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
            # Keep selected items in same field
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            # Allow use to select from selected items
            merge_to = forms.ModelChoiceField(queryset)
        
        if 'merge' in request.POST:
            merge_form = MergeForm(request.POST)
            if merge_form.is_valid():
                merge_to = merge_form.cleaned_data['merge_to']
                merge_to.merge_tags(queryset)
                self.message_user(request, 'Tags merged')
                return HttpResponseRedirect(request.get_full_path())
        else:
            merge_form = MergeForm(
                initial={
                    '_selected_action': request.POST.getlist(
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
    """
    Create a new ModelAdmin for the specified tag model
    """
    if isinstance(model, tag_models.BaseTagDescriptor):
        # It's a tag descriptor; change it for the tag model itself
        model = model.tag_model
    
    if issubclass(model, tag_models.TagTreeModel):
        admin_cls = TagTreeModelAdmin
    else:
        admin_cls = TagModelAdmin
        
    # Default site to admin.site - but here instead of constructor, in the
    # unlikely but possible case that someone changed it during initialisation
    if site is None:
        site = admin.site
    
    # Register with the default TagModelAdmin class
    register(model, admin_class=admin_cls, site=site)
    
