"""
Tagulous model fields

These are the fields which users will add to models. During the
``contribute_to_class`` phase of model initialisation, they create any
necessary tag models, and add the descriptors back onto the model.

They are also responsible for preparing form fields.
"""
from __future__ import unicode_literals

import django
from django.db import models
from django.utils import six
from django.utils.text import capfirst

from tagulous import constants
from tagulous import settings
from tagulous import forms
from tagulous.models.options import TagOptions
from tagulous.models.models import BaseTagModel, TagModel, TagTreeModel
from tagulous.models.descriptors import SingleTagDescriptor, TagDescriptor
from tagulous.utils import render_tags


###############################################################################
####### Mixin for model tag fields
###############################################################################

class BaseTagField(object):
    """
    Mixin for TagField and SingleTagField
    """
    # List of fields which are forbidden from __init__
    forbidden_fields = ()
    
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
        
        # Detect whether we need to automatically generate a tag model
        if self.tag_model:
            self.auto_tag_model = False
            
            # Tag model might be a string - set options later
            self.tag_options = None
            self._deferred_options = [set_tag_meta, options]
            
        else:
            self.auto_tag_model = True
            self.tag_options = TagOptions(**options)
            self._deferred_options = None
        
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
        
        # Make a note that this has not been contributed to a class yet
        self.contributed = False
        
        # This attribute will let us tell South to supress undesired M2M fields
        self.south_supression = True
    
    if django.VERSION < (1, 9):
        remote_field = property(lambda self: self.rel)
    
    def do_related_class(self, other, cls):
        """
        Process tag model now it has been resolved if it was a string
        """
        # Set up relation as normal 
        super(BaseTagField, self).do_related_class(other, cls)
        
        # Make sure tag model is the related model, in case it was a string
        if django.VERSION < (1, 8):
            # Django 1.7 or earlier
            self.tag_model = self.related.parent_model
        else:
            # Django 1.8 or later
            self.tag_model = self.remote_field.model
        
        # Check class type of tag model
        if not issubclass(self.tag_model, BaseTagModel):
            raise ValueError('Tag model must be a subclass of TagModel')
        
        # Process the deferred options
        self._process_deferred_options(is_to_self=self.tag_model == cls)
        
    def _process_deferred_options(self, is_to_self=False):
        """
        Process tag options once we have the related model
        
        If the field is explicitly referring to itself, is_to_self will be True
        """
        # See if tag options were deferred
        if self._deferred_options is None:
            return
        
        # Get deferred options
        set_tag_meta, options = self._deferred_options
        self._deferred_options = None
        
        # Set options
        if options:
            if set_tag_meta:
                # Tag option arguments must be used to update the tag model
                # (and any other tag fields which use it) - used during
                # migration when the tag model doesn't know its own options
                self.tag_model.tag_options.update(options)
            else:
                raise ValueError(
                    'Cannot set tag options on explicit tag model %r' % (
                        self.tag_model,
                    )
                )
        
        # Link to model options by reference in case they get updated later
        self.tag_options = self.tag_model.tag_options
        
    def contribute_to_class(self, cls, name):
        """
        Create the tag model if necessary, then initialise and contribute the
        field to the class
        """
        #
        # Get or create the tag model
        #
        
        # Create a new tag model if we need to
        if self.auto_tag_model:
            # Make sure a TagField is only contributed once if the model is
            # not explicitly set. This isn't normal for model fields, but in
            # this case the name of the model (and therefore db) would depend
            # on the load order, which could change. Rather than risk problems
            # later, ban it outright to save developers from themselves.
            # If it causes problems for anyone, they can explicitly set a tag
            # model and avoid this being a problem.
            if self.contributed:
                raise AttributeError(
                    "The tag field %r is already attached to a model" % self
                )
            
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
            self.tag_model = type(str(model_name), (model_cls,), model_attrs)
            
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
            # If it's a problem, contrib.auth will raise a ValidationError
            
        
        #
        # Build the tag field
        #
        
        # Update the rel on the field
        if django.VERSION < (1, 9):
            # Django 1.8 or earlier
            self.remote_field.to = self.tag_model
        else:
            # Django 1.9 and later
            self.remote_field.model = self.tag_model
        
        # Contribute to class
        super(BaseTagField, self).contribute_to_class(cls, name)
        self.contributed = True
    
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
    
    def deconstruct(self):
        """
        Deconstruct field options to a dict for __init__
        """
        name, path, args, kwargs = super(BaseTagField, self).deconstruct()
        
        # Find tag model options
        if isinstance(self.tag_options, TagOptions):
            # When deconstruct is called on a real field on a real model,
            # we will have a concrete tag model, so use its tag options
            items = self.tag_options.items(with_defaults=False)
            
            # Freeze initial as a string, not array
            if 'initial' in items:
                items['initial'] = self.tag_options.initial_string
            
        elif self._deferred_options is not None:
            # When deconstruct is called on a ModelState field, the options
            # will have been deferred
            set_tag_meta, options = self._deferred_options
            items = options
            
        else: # pragma: no cover
            # It should never get here - raise an exception so we can debug
            raise ValueError('Unexpected state')
        
        # Add tag model options to kwargs
        kwargs.update(items)
        
        # Can't freeze lambdas. It should work if it's a function at the top
        # level of a module, but there's no easy way to differentiate. For
        # safety and consistency, strip callable arguments and mention in
        # documentation.
        if 'get_absolute_url' in kwargs:
            del kwargs['get_absolute_url']
        
        # Remove forbidden fields
        # This shouldn't be needed, but strip them just in case
        for forbidden in self.forbidden_fields: # pragma: no cover
            if forbidden in kwargs:
                del kwargs[forbidden]
            
        # Always store _set_tag_meta=True, so migrating tag fields can set tag
        # models' TagMeta
        kwargs['_set_tag_meta'] = True
        
        return name, path, args, kwargs


###############################################################################
####### Single tag field
###############################################################################

class SingleTagField(BaseTagField, models.ForeignKey):
    """
    Build the tag model and register the TagForeignKey
    Not actually a field - syntactic sugar for creating tag fields
    """
    description = 'A single tag field'
    
    # List of fields which are forbidden from __init__
    forbidden_fields = ('to_field', 'rel_class', 'max_count')
    
    def __init__(self, *args, **kwargs):
        """
        Create a single tag field - a tag field which can only take one tag
        
        See docs/models.rst for a list of arguments
        """
        # Forbid certain ForeignKey arguments
        for forbidden in self.forbidden_fields:
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
        
        # Set default on_delete
        if 'on_delete' not in kwargs:
            kwargs['on_delete'] = models.CASCADE
        
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
        new_descriptor = SingleTagDescriptor(old_descriptor)
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
    
    # List of fields which are forbidden from __init__
    forbidden_fields = ('db_table', 'through', 'symmetrical')
    
    def __init__(self, *args, **kwargs):
        """
        Create a Tag field
        
        See docs/models.rst for a list of arguments
        """
        # Forbid certain ManyToManyField arguments
        for forbidden in self.forbidden_fields:
            if forbidden in kwargs:
                raise ValueError(
                    "Invalid argument '%s' for TagField" % forbidden
                )
        
        # Note things we'll need to restore after __init__
        help_text = kwargs.pop('help_text', '')
        
        super(TagField, self).__init__(*args, **kwargs)
        
        # Change default help text
        self.help_text = help_text or 'Enter a comma-separated tag string'
        
    def contribute_to_class(self, cls, name):
        """
        Create the related tag model, initialise the ManyToManyField with it,
        and set up the model to use the TagDescriptor
        """
        # Standard BaseTagField contribute
        super(TagField, self).contribute_to_class(cls, name)
        
        # Replace the descriptor with our own
        old_descriptor = getattr(cls, name)
        new_descriptor = TagDescriptor(old_descriptor)
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
