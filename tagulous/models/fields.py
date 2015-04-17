"""
Tagulous model fields

These are the fields which users will add to models. During the
``contribute_to_class`` phase of model initialisation, they create any
necessary tag models, and add the descriptors back onto the model.

They are also responsible for preparing form fields.
"""

from django.db import models
from django.utils.text import capfirst

from tagulous import constants
from tagulous import settings
from tagulous import forms
from tagulous.models.options import TagOptions
from tagulous.models.models import TagModel
from tagulous.models.descriptors import SingleTagDescriptor, TagDescriptor
from tagulous.utils import render_tags


###############################################################################
####### Mixin for model tag fields
###############################################################################

class BaseTagField(object):
    """
    Mixin for TagField and SingleTagField
    """
    def init_tagfield(self, to=None, **kwargs):
        # Save tag model
        self.tag_model = to
        
        # See if this tag model is to be auto-generated
        # If manual, collect options from TagMeta
        tag_meta = {}
        if self.tag_model:
            self.auto_tag_model = False
            
            # Get ancestors' TagMeta options, oldest first
            for klass in reversed(self.tag_model.mro()):
                if 'TagMeta' in klass.__dict__:
                    for key in constants.OPTION_DEFAULTS.keys():
                        if key in klass.TagMeta.__dict__:
                            tag_meta[key] = getattr(klass.TagMeta, key)
        else:
            self.auto_tag_model = True
        
        # Extract options
        options = {}
        for key, default in constants.OPTION_DEFAULTS.items():
            # Look in kwargs, then in tag_meta
            if key in kwargs:
                options[key] = kwargs.pop(key)
            elif key in tag_meta:
                options[key] = tag_meta[key]
        
        # Create tag options
        self.tag_options = TagOptions(**options)
        
        # If there's a tag model, ensure tag_options are there
        if self.tag_model and not hasattr(self.tag_model, 'tag_options'):
            self.tag_model.tag_options = self.tag_options
        
        # Note things we'll need to restore after __init__
        help_text = kwargs.pop('help_text', '')
        
        # If the tag model was not specified, we need to specify one.
        # However, we can't reliably auto-generate a unique and repeatable
        # model name for tags here in __init__ - we can only do that in
        # contribute_to_class once we know the name of the field in the model.
        # We'll therefore use the string '-'; Django will not do anything about
        # resolving it until contribute_to_class, at which point we'll replace
        # it with a reference to the real tag model.
        kwargs['to'] = self.tag_model if self.tag_model else '-'
        
        # Call super __init__
        super(BaseTagField, self).__init__(**kwargs)
        
        # Change default help text
        self.help_text = help_text or 'Enter a comma-separated tag string'
        
        # Make a note that this has not been contributed to a class yet
        self.contributed = False
        
        # This attribute will let us tell South to supress undesired M2M fields
        self.south_supression = True
    
    def contribute_tagfield(self, cls, name):
        """
        Create the tag model if necessary, then initialise and contribute the
        field to the class
        """
        #
        # Get or create the tag model
        #
        
        # Make sure a TagField is only contributed once
        # Otherwise the name of the model (and therefore db) would depend on
        # the load order, which could change. Rather than risk problems later,
        # ban it outright to save developers from themselves
        if self.contributed:
            raise AttributeError("Cannot contribute a TagField to a model more than once.")
        self.contributed = True
        
        # Create a new tag model if we need to
        if self.auto_tag_model:
            # Generate a list of attributes for the new tag model
            model_attrs = {
                # Module should be the same as the main model
                '__module__': cls.__module__,
                
                # Give it access to the options
                'tag_options': self.tag_options,
            }
            
            # Build new tag model
            # Name is _Tagulous_MODELNAME_FIELDNAME
            model_name = "%s_%s_%s" % (
                constants.MODEL_PREFIX, cls._meta.object_name, name,
            )
            self.tag_model = type(model_name, (TagModel,), model_attrs)
            
            # Give it a verbose name, for admin filters
            verbose_name = '%s %s tag' % (cls._meta.object_name, name)
            self.tag_model._meta.verbose_name = verbose_name
            self.tag_model._meta.verbose_name_plural = verbose_name + 's'
        # else: tag model already specified
        
        
        #
        # Build the tag field
        #
        
        # Update the rel on the field
        self.rel.to = self.tag_model
        
        # Contribute to class
        super(BaseTagField, self).contribute_to_class(cls, name)
    
    def tag_formfield(self, form_class, **kwargs):
        """
        Common actions for TagField and SingleTagField to set up a formfield
        """
        required = not self.blank
        if hasattr(self, 'required'):
            required = self.required
        
        # Update tag options, if necessary
        tag_options = self.tag_options
        if 'tag_options' in kwargs:
            tag_options += kwargs.pop('tag_options')
        
        # Start off with defaults
        options = {
            # Arguments the TagField base (CharField) would expect
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
            "required": required,
            
            # Also pass tag options
            "tag_options": tag_options
        }
        
        # Update with kwargs
        options.update(kwargs)
        
        # Add in list of tags for autocomplete, if appropriate
        if 'autocomplete_tags' in kwargs:
            options['autocomplete_tags'] = kwargs['autocomplete_tags']
        elif 'autocomplete_view' not in kwargs:
            options['autocomplete_tags'] = self.tag_model.objects.order_by('name')
        
        # Create the field instance
        return form_class(**options)

    def get_manager_name(self):
        """
        Get the field name for the Manager
        """
        return "_%s_tagulous" % self.name


###############################################################################
####### Single tag field
###############################################################################

class SingleTagField(BaseTagField, models.ForeignKey):
    """
    Build the tag model and register the TagForeignKey
    Not actually a field - syntactic sugar for creating tag fields
    """
    description = 'A single tag field'
    
    def __init__(self, *args, **kwargs):
        """
        Create a single tag field - a tag field which can only take one tag
        
        See docs/models.rst for a list of arguments
        """
        # Forbid certain ForeignKey arguments
        for forbidden in ['to_field', 'rel_class', 'max_count']:
            if forbidden in kwargs:
                raise ValueError("Invalid argument '%s' for SingleTagField" % forbidden)
        
        kwargs['max_count'] = 1
        
        # TagFields will need to be nulled in the database when deleting,
        # regardless of whether we want to allow them to be null or not.
        # Make a note of whether this is required.
        self.required = not kwargs.pop('blank', False)
        kwargs['blank'] = True
        kwargs['null'] = True
        
        # Create the tag field
        self.init_tagfield(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        """
        Create the related tag model, initialise the ForeignKey with it,
        and set up the model to use the SingleTagDescriptor instead of the
        ReverseSingleRelatedObjectDescriptor
        """
        # Standard contribute
        self.contribute_tagfield(cls, name)
        
        # Replace the descriptor with our own
        old_descriptor = getattr(cls, name)
        new_descriptor = SingleTagDescriptor(old_descriptor, self.tag_options)
        setattr(cls, name, new_descriptor)
        
    def value_from_object(self, obj):
        """
        Returns the value of the foreign key as a tag string
        """
        tag = getattr(obj, self.name)
        if tag:
            return render_tags([tag.name])
        return ''
        
    def formfield(self, form_class=forms.SingleTagField, **kwargs):
        """
        Create the form field
        For arguments see forms.TagField
        """
        return self.tag_formfield(form_class=form_class, **kwargs)

        
###############################################################################
####### Tag field
###############################################################################

class TagField(BaseTagField, models.ManyToManyField):
    """
    Build the tag model and register the TagManyToManyField
    Not actually a field - syntactic sugar for creating tag fields
    Will not allow a through table
    """
    description = 'A tag field'
    
    def __init__(self, *args, **kwargs):
        """
        Create a Tag field
        
        See docs/models.rst for a list of arguments
        """
        # Forbid certain ManyToManyField arguments
        for forbidden in ['db_table', 'through', 'symmetrical']:
            if forbidden in kwargs:
                raise ValueError("Invalid argument '%s' for TagField" % forbidden)
        
        self.init_tagfield(*args, **kwargs)
        
    def contribute_to_class(self, cls, name):
        """
        Create the related tag model, initialise the ManyToManyField with it,
        and set up the model to use the TagDescriptor
        """
        # Standard contribute
        self.contribute_tagfield(cls, name)
        
        # Replace the descriptor with our own
        old_descriptor = getattr(cls, name)
        new_descriptor = TagDescriptor(old_descriptor, self.tag_options)
        setattr(cls, name, new_descriptor)
        
    def value_from_object(self, obj):
        """
        Tricks django.forms.models.model_to_dict into passing data to the form.
        
        Because the models.TagField is based on a django ManyToManyField,
        model_to_dict expects a queryset, which it changes to a list of pks
        for use in a ModelMultipleChoiceField.
        
        Instead, we want to pass the tag string to a forms.TagField, which is a
        subclass of CharField. We can't do this in the TagField itself because
        there's no model context by that stage to do the pk lookup.
        
        We therefore return a fake queryset containing a single fake item,
        where the pk attribute is the tag string.
        
        It's a bit of a hack to avoid monkey-patching django, but this may
        leave it vulnerable to changes in future versions of Django.
        """
        class FakeObject(object):
            """
            FakeObject so m2d can check obj.pk (django <= 1.4)
            """
            def __init__(self, value):
                self.pk = value
        
        class FakeQuerySet(object):
            """
            FakeQuerySet so m2d can call qs.values_list() (django >= 1.5)
            Only contains one FakeObject instance
            """
            def __init__(self, obj):
                self.obj = obj
                
            def __iter__(self):
                """
                Iterable so m2d can use in list comprehension (django <= 1.4)
                """
                yield self.obj
            
            def values_list(self, *fields, **kwargs):
                """
                Ignores arguments and returns an empty list with the object.pk
                """
                return [self.obj.pk]
        
        return FakeQuerySet(FakeObject(
            getattr(obj, self.attname).get_tag_string()
        ))
        
        
    def formfield(self, form_class=forms.TagField, **kwargs):
        """
        Create the form field
        For arguments see forms.TagField
        """
        return self.tag_formfield(form_class=form_class, **kwargs)

    def save_form_data(self, instance, data):
        """
        When the form wants to save this data, it will only be doing so after
        the instance has been saved. This must be committed to the database.
        """
        setattr(instance, self.attname, data)
        getattr(instance, self.attname).save()
