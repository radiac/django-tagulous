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
from tagulous.models.models import TagModel, TagTreeModel
from tagulous.models.descriptors import SingleTagDescriptor, TagDescriptor
from tagulous.utils import render_tags


###############################################################################
####### Mixin for model tag fields
###############################################################################

class BaseTagField(object):
    """
    Mixin for TagField and SingleTagField
    """
    def __init__(self, to=None, **kwargs):
        """
        Initialise the tag options and store 
        
        Takes all tag options as keyword arguments, as long as there is no
        ``to`` tag model specified.
        
        Undocumented keyword argument ``_set_tag_meta`` is used internally to
        update tag model options with those specified in keyword arguments when
        a ``to`` tag model is specified. However, this is intended for internal
        use only (when migrating), so if you must use it, use it with care.
        """
        # Save tag model
        self.tag_model = to
        
        # Extract options from kwargs
        options = {}
        for key, default in constants.OPTION_DEFAULTS.items():
            # Look in kwargs, then in tag_meta
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Detect if _set_tag_meta is set
        set_tag_meta = kwargs.pop('_set_tag_meta', False)
        
        # Decide what to do with tag options
        if self.tag_model:
            if options:
                if set_tag_meta:
                    # Tag option arguments must be used to update the tag model
                    # (and any other tag fields which use it) - used during
                    # migration when the tag model doesn't know its own options
                    self.tag_model.tag_options.update(options)
                else:
                    raise ValueError(
                        'Cannot set tag options %s on explicit tag model %r' % (
                            ', '.join(repr(k) for k in options.keys()),
                            self.tag_model,
                        )
                    )
            
            self.auto_tag_model = False
            # Link to model options by reference in case they get updated later
            self.tag_options = self.tag_model.tag_options
        else:
            self.tag_options = TagOptions(**options)
            self.auto_tag_model = True
        
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
    
    def contribute_to_class(self, cls, name):
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
            raise AttributeError(
                "The tag field %r is already attached to a model" % self
            )
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
            model_cls = TagModel
            if self.tag_options.tree:
                model_cls = TagTreeModel
            self.tag_model = type(model_name, (model_cls,), model_attrs)
            
            # Give it a verbose name, for admin filters
            verbose_name_singular = (
                self.tag_options.verbose_name_singular or self.verbose_name or name
            )
            verbose_name_plural = self.tag_options.verbose_name_plural
            if not verbose_name_plural:
                verbose_name_plural = (
                    verbose_name_singular or self.verbose_name or name
                )
                if not verbose_name_plural.endswith('s'):
                    verbose_name_plural += 's'
            
            # Get object verbose name
            object_name = cls._meta.verbose_name
            self.tag_model._meta.verbose_name = '%s %s' % (
                object_name, verbose_name_singular,
            )
            self.tag_model._meta.verbose_name_plural = '%s %s' % (
                object_name, verbose_name_plural,
            )
            
            # Make no attempt to enforce max length of verbose_name - no good
            # automatic solution, and the limit may change, see
            #   https://code.djangoproject.com/ticket/17763
            # If it's a problem, contrib.auth with raise a ValidationError
            
        
        #
        # Build the tag field
        #
        
        # Update the rel on the field
        self.rel.to = self.tag_model
        
        # Contribute to class
        super(BaseTagField, self).contribute_to_class(cls, name)
    
    def formfield(self, form_class, **kwargs):
        """
        Common actions for TagField and SingleTagField to set up a formfield
        """
        required = not self.blank
        if hasattr(self, 'required'):
            required = self.required
        
        # Update tag options, if necessary
        tag_options = self.tag_options
        if 'tag_options' in kwargs:
            new_options = kwargs.pop('tag_options')
            if not isinstance(new_options, TagOptions):
                new_options = TagOptions(**new_options)
            tag_options += new_options
        
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
        elif not tag_options.autocomplete_view:
            tags = self.tag_model.objects.all()
            if tag_options.autocomplete_initial:
                tags = tags.initial()
            options['autocomplete_tags'] = tags
        
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
                raise ValueError(
                    "Invalid argument '%s' for SingleTagField" % forbidden
                )
        
        # TagFields will need to be nulled in the database when deleting,
        # regardless of whether we want to allow them to be null or not.
        # Make a note of whether this is required.
        self.required = not kwargs.pop('blank', False)
        kwargs['blank'] = True
        kwargs['null'] = True
        
        # Create the tag field
        super(SingleTagField, self).__init__(*args, **kwargs)
        
    def contribute_to_class(self, cls, name):
        """
        Create the related tag model, initialise the ForeignKey with it,
        and set up the model to use the SingleTagDescriptor instead of the
        ReverseSingleRelatedObjectDescriptor
        """
        # Standard BaseTagField contribute
        super(SingleTagField, self).contribute_to_class(cls, name)
        
        # Replace the descriptor with our own
        old_descriptor = getattr(cls, name)
        new_descriptor = SingleTagDescriptor(old_descriptor, self.tag_options)
        setattr(cls, name, new_descriptor)
        
    def value_from_object(self, obj):
        """
        Returns the value of the foreign key as a tag string, for a form
        """
        tag = getattr(obj, self.name)
        if tag:
            return tag.name
        return ''
        
    def formfield(self, form_class=forms.SingleTagField, **kwargs):
        """
        Create the form field
        For arguments see forms.TagField
        """
        return super(SingleTagField, self).formfield(
            form_class=form_class, **kwargs
        )


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
                raise ValueError(
                    "Invalid argument '%s' for TagField" % forbidden
                )
        
        super(TagField, self).__init__(*args, **kwargs)
        
    def contribute_to_class(self, cls, name):
        """
        Create the related tag model, initialise the ManyToManyField with it,
        and set up the model to use the TagDescriptor
        """
        # Standard BaseTagField contribute
        super(TagField, self).contribute_to_class(cls, name)
        
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
        where the pk attribute is the tag string - a bit of a hack, but avoids
        monkey-patching Django.
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
                self._result_cache = None
                
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
        return super(TagField, self).formfield(
            form_class=form_class, **kwargs
        )

    def save_form_data(self, instance, data):
        """
        When the form wants to save this data, it will only be doing so after
        the instance has been saved. This must be committed to the database.
        """
        setattr(instance, self.attname, data)
        getattr(instance, self.attname).save()


###############################################################################
####### Field util methods
###############################################################################

def singletagfields_from_model(model):
    """
    Get a list of SingleTagField fields from a model class
    """
    return [
        field for field in model._meta.fields
        if isinstance(field, SingleTagField)
    ]

def tagfields_from_model(model):
    """Get a list of TagField fields from a model class"""
    return [
        field for field in model._meta.many_to_many
        if isinstance(field, TagField)
    ]
