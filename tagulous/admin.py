from django import forms
from django.contrib import admin
from django.conf.urls import patterns, include, url
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models.base import ModelBase
from django.shortcuts import render
from django.http import HttpResponseRedirect

from tagulous import models as tag_models
from tagulous import forms as tag_forms
from tagulous import settings as tag_settings


###############################################################################
########################################################### Admin registration
###############################################################################

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
    # Get a list of all tag fields
    #
    
    # Dict of single tag fields, {name: tag}
    single_tag_fields = {}
    
    # Dict of normal tag fields, {name: tag}
    tag_fields = {}
    
    # List of all single and normal tag fields
    tag_field_names = []
    
    # Check for SingleTagField related fields
    for field in model._meta.fields:
        if isinstance(field, tag_models.SingleTagField):
            single_tag_fields[field.name] = field
            tag_field_names.append(field.name)
    
    # Check for TagField m2m fields
    for field in model._meta.many_to_many:
        if isinstance(field, tag_models.TagField):
            tag_fields[field.name] = field
            tag_field_names.append(field.name)
    
    
    #
    # Set up tag support
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
                    setattr(admin_class, display_name, create_display(field))
    
    
    # Ensure every tag field uses the correct widgets
    add_formfield_overrides(admin_class)
    
    # Check for inlines
    if hasattr(admin_class, 'inlines'):
        for inline in admin_class.inlines:
            add_formfield_overrides(inline)
    
    # Register the model
    site.register(model, admin_class)
    
    
def add_formfield_overrides(cls):
    """
    Extend formfield to ensure every tag field uses the correct widgets
    """
    if not cls.formfield_overrides:
        cls.formfield_overrides = {}
        
    if tag_models.SingleTagField not in cls.formfield_overrides:
        cls.formfield_overrides[tag_models.SingleTagField] = {
            'widget': tag_forms.AdminTagWidget,
        }
        
    if tag_models.TagField not in cls.formfield_overrides:
        cls.formfield_overrides[tag_models.TagField] = {
            'widget': tag_forms.AdminTagWidget,
        }
    
    
def create_display(field):
    def display(self, obj):
        return getattr(obj, field).get_tag_string()
    display.short_description = field.replace('_', ' ')
    return display



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

def tag_model(model, site=None):
    """
    Create a new ModelAdmin for the specified tag model
    """
    if isinstance(model, tag_models.BaseTagDescriptor):
        # It's a tag descriptor; change it for the tag model itself
        model = model.tag_model
        
    # Default site to admin.site - but here instead of constructor, in the
    # unlikely but possible case that someone changed it during initialisation
    if site is None:
        site = admin.site
    
    # Register with the default TagModelAdmin class
    register_site(site, model, admin_class=TagModelAdmin)
    
    print "Model now", model


###############################################################################
############################################################ Disable admin add
###############################################################################

def monkeypatch_formfield_for_dbfield():
    """
    This will monkey-patch BaseModelAdmin.formfield_for_dbfield to remove
    a RelatedFieldWidgetWrapper from an AdminTagWidget created for a
    SingleTagField or TagField
    """
    old = admin.options.BaseModelAdmin.formfield_for_dbfield
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = old(self, db_field, **kwargs)
        if (
            isinstance(db_field, (tag_models.SingleTagField, tag_models.TagField))
            and
            isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper)
            and
            isinstance(formfield.widget.widget, tag_forms.AdminTagWidget)
        ):
            formfield.widget = formfield.widget.widget
        return formfield
    
    # Monkeypatch
    admin.options.BaseModelAdmin.formfield_for_dbfield = formfield_for_dbfield
    
if tag_settings.DISABLE_ADMIN_ADD:
    monkeypatch_formfield_for_dbfield()
