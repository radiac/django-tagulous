import sys

import django
from django.core.urlresolvers import reverse
from django.core import exceptions
from django.db import models, router
from django.db.utils import DatabaseError
from django.db.models.signals import pre_save, post_syncdb
from django.dispatch import receiver
from django.utils.text import capfirst

from tagulous import constants
from tagulous import forms
from tagulous.models.options import TagOptions
from tagulous.utils import parse_tags, render_tags


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
    for field in model._meta.fields + model._meta.many_to_many:
        if isinstance(
            field,
            (SingleTagField, TagField)
        ):
            field_initialise_tags(model, field, report)


#
# Abstract base class for all TagModel models
#
class BaseTagModel(models.Model):
    """
    Base tag model, without fields
    Required for South
    """
    def __unicode__(self):
        return u'%s' % self.name
        
    def update_count(self, count):
        """
        Update the count, then either save or delete the tag as appropriate
        """
        self.count = count
        if count == 0 and not self.protected and not self.tag_options.protect_all:
            self.delete()
        else:
            self.count = count
            self.save()
    
    def increment(self):
        """
        Increase the count by one
        """
        self.update_count(self.count + 1)
    
    def decrement(self):
        """
        Decrease the count by one
        """
        self.update_count(self.count - 1)
    
    def __eq__(self, obj):
        """
        If comparing to a string, is equal if string value matches
        Otherwise compares normally
        """
        if isinstance(obj, basestring):
            return self.name == obj
        return super(BaseTagModel, self).__eq__(obj)

    def __ne__(self, obj):
        return not self == obj
    
    def merge_tags(self, tags):
        """
        Merge the specified tags into this tag
        """
        model = self.model
        meta = model._meta
        if hasattr(meta, 'get_fields'):
            # Django 1.8
            related_fields = meta.get_fields(include_hidden=True)
        else:
            related_fields = meta.get_all_related_objects()
            related_fields += meta.get_all_related_many_to_many_objects()
        
        # Ensure tags is a list of tag instances
        if not isinstance(tags, models.query.QuerySet):
            tags = model.objects.filter(name__in=tags)
            
        # Make sure self isn't in tags
        tags = tags.exclude(pk=self.pk)
        
        for related in related_fields:
            # Get the related instances for this field
            objs = related.model._base_manager.using(
                router.db_for_write(self.model)
            ).filter(
                **{"%s__in" % related.field.name: tags}
            )
            
            # Switch the tags
            if isinstance(related.field, SingleTagField):
                for obj in objs:
                    setattr(obj, related.field.name, self)
                    obj.save()
                    
            elif isinstance(related.field, TagField):
                for obj in objs:
                    getattr(obj, related.field.name).remove(*tags)
                    getattr(obj, related.field.name).add(self)
        
    class Meta:
        abstract = True
        
        
class TagModel(BaseTagModel):
    """
    Abstract base class for tag models
    """
    name        = models.CharField(max_length=255, unique=True)
    count       = models.IntegerField(default=0,
        help_text="Internal counter to keep track of how many relationships there are"
    )
    protected   = models.BooleanField(default=False,
        help_text="Will not be deleted when the count reaches 0"
    )
    
    # For consistency with SingleTagField, provide .model attribute
    model = property(lambda self: self.__class__)
    
    class Meta:
        abstract = True

        
#
# Descriptors for originating models
# Return a tag-aware manager
#

class BaseTagDescriptor(object):
    """
    Base TagDescriptor class
    """
    def __init__(self, descriptor, tag_options):
        # Store arguments
        self.descriptor = descriptor
        self.tag_options = tag_options
        
        # Copy descriptor attributes
        for key, val in descriptor.__dict__.items():
            setattr(self, key, val)
            
        # Add a convenient reference to the tag model
        self.model = self.field.rel.to
        
    def load_initial(self):
        """
        Load initial tags
        Be prepared to receive a DatabaseError if the model has not been synced
        """
        for tag_name in self.tag_options.initial:
            self.model.objects.get_or_create(name=tag_name, defaults={
                'protected': self.tag_options.protect_initial,
            })
            
            
class BaseTagManager(object):
    """
    Base class for SingleTagManager and RelatedManagerTagMixin
    """
    def __eq__(self, other):
        """
        Treat the other value as a string and compare to tags
        """
        other_str = u"%s" % other
        
        # Enforce case non-sensitivity or lowercase
        lower = False
        if self.tag_options.force_lowercase or not self.tag_options.case_sensitive:
            lower = True
            other_str = other_str.lower()
        
        # Parse other_str into list of tags
        other_tags = parse_tags(other_str)
        
        # Get list of set tags
        self_tags = self.get_tag_list()
        
        # Compare tag count
        if len(other_tags) != len(self_tags):
            return False
        
        # ++ Could optimise comparison for lots of tags by using an object
        
        # Compare tags
        for tag in self_tags:
            # If lowercase or not case sensitive, lower for comparison
            if lower:
                tag = tag.lower()
            
            # Check tag in other tags
            if tag not in other_tags:
                return False
        
        # Same number of tags, and all self tags present in other tags
        # It's a match
        return True
        
    def __ne__(self, other):
        return not self.__eq__(other)
        

# ++ Test single tag manager
class SingleTagManager(BaseTagManager):
    """
    Manage single tags - behaves like a descriptor, but holds additional
    information about the tag field between saves
    """
    def __init__(self, descriptor, instance):
        # The SingleTagDescriptor and instance this manages
        self.descriptor = descriptor
        self.instance = instance
        
        # Other vars we need
        self.tag_model = self.descriptor.model
        self.field = self.descriptor.field
        self.tag_options = self.descriptor.tag_options
        
        # Keep track of unsaved changes
        self.changed = False
        
        # The descriptor stores an unsaved tag string
        # Start of with the actual value, if it exists
        self.tag_cache = self.get_actual()
        self.tag_name = self.tag_cache.name if self.tag_cache else None
        
        # Pre/post save will need to keep track of an old tag
        self.removed_tag = None
        
    def flush_actual(self):
        # Flush the cache of actual
        cache_name = self.field.get_cache_name()
        if hasattr(self.instance, cache_name):
            delattr(self.instance, cache_name)
        
    def get_actual(self):
        # A ForeignKey would be on the .attname (field_id), but only
        # if it has been set, otherwise the attribute will not exist
        
        # ++ Init should not be calling this in django's normal world
        # ++ So we need to either stop doing that, or add a flag to get_actual
        # which only tests if the instance exists, or value!=None
        # ++ Think this is fixed now?
        if hasattr(self.instance, self.field.attname):
        #if getattr(self.instance, self.field.attname, None):
            return self.descriptor.descriptor.__get__(self.instance)
        return None
    
    def set_actual(self, value):
        return self.descriptor.descriptor.__set__(self.instance, value)
        
    
    def get_tag_string(self):
        """
        Get the tag edit string for this instance as a string
        """
        if not self.instance:
            raise AttributeError("Function get_tag_string is only accessible via an instance")
        
        return render_tags( self.get() )
    
    def get_tag_list(self):
        """
        Get the tag names for this instance as a list of tag names
        """
        if not self.instance:
            raise AttributeError("Function get_tag_list is only accessible via an instance")
        
        return [tag.name for tag in self.get() ]
        
    def get(self):
        """
        Get the current tag - either a Tag object or None
        If the field has been changed since the instance was last saved, the
        Tag object may be a dynamically generated Tag which does not exist in
        the database yet. The count will not be updated until the instance is
        next saved.
        """
        # If changed, find the tag
        if self.changed:
            if not self.tag_name:
                return None
            
            # Try to look up the tag
            try:
                if self.tag_options.case_sensitive:
                    tag = self.tag_model.objects.get(name=self.tag_name)
                else:
                    tag = self.tag_model.objects.get(name__iexact=self.tag_name)
            except self.tag_model.DoesNotExist, e:
                # Does not exist yet, create a temporary one (but don't save)
                if not self.tag_cache:
                    self.tag_cache = self.tag_model(name=self.tag_name, protected=False)
                tag = self.tag_cache
            return tag
        else:
            # Return the response that it should have had (a Tag or None)
            return self.get_actual()
        
    def set(self, value):
        """
        Set the current tag
        """
        # Parse a tag string
        if not value:
            tag_name = ''
            
        elif isinstance(value, basestring):
            # Force tag to lowercase
            if self.tag_options.force_lowercase:
                value = value.lower()
                
            # Remove quotes from value to ensure it's a valid tag string
            tag_name = value.replace('"', '') or None
            
        # Look up the tag name
        else:
            tag_name = value.name
        
        # If no change, do nothing
        if self.tag_name == tag_name:
            return
        
        # Store the tag name and mark changed
        self.changed = True
        self.tag_name = tag_name
        self.tag_cache = None
        
    def pre_save_handler(self):
        """
        When the model is about to save, update the tag value
        """
        # Get the new tag
        new_tag = self.get()
        
        # Logic check to replace standard null/blank model field validation
        if not new_tag and self.field.required:
            raise exceptions.ValidationError(self.field.error_messages['null'])
        
        # Only need to go further if there has been a change
        if not self.changed:
            return
        
        # Store the old tag so we know to decrement it in post_save
        self.flush_actual()
        self.removed_tag = self.get_actual()
        
        # Create or increment the tag object
        if new_tag:
            # Ensure it is in the database
            if not new_tag.pk:
                new_tag.save()
                
            # Increment the new tag
            new_tag.increment()
        
        # Set it
        self.set_actual(new_tag)
        
        # Clear up
        self.changed = False
        
    def post_save_handler(self):
        """
        When the model has saved, decrement the old tag
        """
        if self.removed_tag:
            self.removed_tag.decrement()
            
    def post_delete_handler(self):
        """
        When the model has been deleted, decrement the actual tag
        """
        # Decrement the actual tag
        self.flush_actual()
        old_tag = self.get_actual()
        if old_tag:
            old_tag.decrement()
            self.set_actual(None)
            
            # If there is no new value, mark the old one as a new one,
            #  so the database will be updated if the instance is saved again
            if not self.changed:
                self.tag_name = old_tag.name
            self.tag_cache = None
            self.changed = True
        
        
class SingleTagDescriptor(BaseTagDescriptor):
    """
    Descriptor to set the tag string rather than a Tag object
    Wraps the ReverseSingleRelatedObjectDescriptor and passes set and get
    requests through to the SingleTagManager
    """
    def __init__(self, descriptor, tag_options):
        super(SingleTagDescriptor, self).__init__(descriptor, tag_options)
        
        # The manager needs to know when the model is about to be saved
        # so that it can ensure the tag exists and assign its pk to field_id
        def pre_save_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.pre_save_handler()
        models.signals.pre_save.connect(pre_save_handler, sender=self.field.model, weak=False)
        
        # The manager needs to know after the model has been saved, so it can
        # decrement the old tag without risk of cascading the delete if count=0
        def post_save_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.post_save_handler()
        models.signals.post_save.connect(post_save_handler, sender=self.field.model, weak=False)
        
        # Update tag count on delete
        def post_delete_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.post_delete_handler()
        models.signals.post_delete.connect(post_delete_handler, sender=self.field.model, weak=False)
        
    def get_manager(self, instance):
        """
        Get the SingleTagManager instance for this field on this model instance
        """
        # Get existing or create new SingleTagManager
        attname = self.descriptor.field.get_manager_name()
        manager = getattr(instance, attname, None)
        if not manager:
            manager = SingleTagManager(self, instance)
            setattr(instance, attname, manager)
        return manager
        
    def __get__(self, instance, instance_type=None):
        # If no instance, return self
        if not instance:
            return self
        
        # Otherwise get from the manager
        manager = self.get_manager(instance)
        return manager.get()
        
    def __set__(self, instance, value):
        # Check we can do this
        # descriptor.__set__() will do this again, but can't be avoided
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")
        
        # Otherwise set on the manager
        manager = self.get_manager(instance)
        manager.set(value)
        
        
class TagDescriptor(BaseTagDescriptor):
    """
    Descriptor to add tag functions to the RelatedManager
    The ManyToManyField will create a ReverseManyRelatedObjectsDescriptor
    This will use a RelatedManager which we cannot customise
    This will intercept calls for the RelatedManager, and add the tag functions
    """
    def __init__(self, descriptor, tag_options):
        super(TagDescriptor, self).__init__(descriptor, tag_options)
        
        # When deleting an instance, Django does not call the add/remove of the
        # M2M manager, so tag counts would be too high. Related to:
        #   https://code.djangoproject.com/ticket/6707
        # We need to clear the M2M manually to update tag counts
        def pre_delete_handler(sender, instance, **kwargs):
            """
            Safely clear the M2M tag field
            """
            # Get the manager and tell it to clear
            manager = self.__get__(instance)
            manager.clear()
        models.signals.pre_delete.connect(pre_delete_handler,
            sender=self.field.model, weak=False
        )
        
    def __get__(self, instance, instance_type=None):
        # If no instance, return self
        if not instance:
            return self
        
        # Get the RelatedManager that should have been returned
        manager = self.descriptor.__get__(instance, instance_type)
        
        # Add in the mixin
        # Thanks, http://stackoverflow.com/questions/8544983/dynamically-mixin-a-base-class-to-an-instance-in-python
        manager.__class__ = type('TagRelatedManager',
            (manager.__class__, RelatedManagerTagMixin),
            {}
        )
        
        # Switch add, remove and clear out, keeping the old versions to call later
        manager._old_add,    manager.add    = manager.add,    manager._add
        manager._old_remove, manager.remove = manager.remove, manager._remove
        manager._old_clear,  manager.clear  = manager.clear,  manager._clear
        
        # Add options to manager
        manager.tag_options = self.tag_options
        
        return manager

    def __set__(self, instance, value):
        # Check we can do this
        # descriptor.__set__() will do this again, but can't be avoided
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")
        
        # Get the manager
        manager = self.__get__(instance)
        
        # Set value
        if not value:
            # Clear
            manager.clear()
        
        elif isinstance(value, basestring):
            # If it's a string, it must be a tag string
            manager.set_tag_string(value)
        
        elif isinstance(value, (list, tuple)) and isinstance(value[0], basestring):
            # It's a list of tuple of tag names
            manager.set_tag_list(value)
        
        
        elif isinstance(value, RelatedManagerTagMixin):
            ##24# ++ Why does this clear first? Unnecessary?
            manager.clear()
            manager.set_tag_list(value.get_tag_list())
        
        else:
            ##24# ++ Handle a list of Tag instances, or a queryset of Tags
            # ++ This is a risky fallthrough
            # ++ The intention is to set a list of TagModel instances
            # ++ But that needs to be explicitly tested here
            # ++ Causes problems when trying to save a queryset from a different tagmodel
            manager.clear()
            manager.add(*value)
        
        
class RelatedManagerTagMixin(BaseTagManager):
    """
    Mixin for RelatedManager to add tag functions
    """
    #
    # New add, remove and clear, to update tag counts
    # Will be switched into place by TagDescriptor
    #
    def _add(self, *objs):
        self._old_add(*objs)
        for tag in objs:
            tag.increment()
    _add.alters_data = True
    
    def _remove(self, *objs):
        self._old_remove(*objs)
        for tag in objs:
            tag.decrement()
    _remove.alters_data = True

    def _clear(self):
        tags = list(self.all())
        self._old_clear()
        for tag in tags:
            tag.decrement()
    _clear.alters_data = True
    
        
    #
    # Functions for getting and setting tags
    #
    
    def get_tag_string(self):
        """
        Get the tag edit string for this instance as a string
        """
        if not self.instance:
            raise AttributeError("Function get_tag_string is only accessible via an instance")
        
        return render_tags( self.all() )
    
    def get_tag_list(self):
        """
        Get the tag names for this instance as a list of tag names
        """
        # ++ Better as get_tag_strings?
        if not self.instance:
            raise AttributeError("Function get_tag_list is only accessible via an instance")
        
        return [tag.name for tag in self.all() ]
        
    def set_tag_string(self, tag_string):
        """
        Sets the tags for this instance, given a tag edit string
        """
        if not self.instance:
            raise AttributeError("Function set_tag_string is only accessible via an instance")
        
        # Get all tag names
        tag_names = parse_tags(tag_string)
        
        # Pass on to set_tag_list
        return self.set_tag_list(tag_names)
    set_tag_string.alters_data = True
        
    def set_tag_list(self, tag_names):
        """
        Sets the tags for this instance, given a list of tag names
        """
        if not self.instance:
            raise AttributeError("Function set_tag_list is only accessible via an instance")
        
        if self.tag_options.max_count and len(tag_names) > self.tag_options.max_count:
            raise ValueError("Cannot set more than %d tags on this field" % self.tag_options.max_count)
        
        # Force tag_names to unicode strings, just in case
        tag_names = [u'%s' % tag_name for tag_name in tag_names]
        
        # Find tag model
        tag_model = self.model
        
        # Get list of current tags
        old_tags = self.all()
        
        # See which tags are staying and which are being removed
        current_names = []
        for tag in old_tags:
            # If a tag is not in the new list, remove it
            if tag.name not in tag_names:
                self.remove(tag)
                
            # Otherwise note it
            else:
                current_names.append(tag.name)
        
        # Find or create these tags
        for tag_name in tag_names:
            # Force tags to lowercase
            if self.tag_options.force_lowercase:
                tag_name = tag_name.lower()
            
            # If this is already in there, don't do anything
            if tag_name in current_names:
                continue
            
            # Find or create the tag
            # Do it manually, there's a problem with get_or_create, iexact and unique
            try:
                if self.tag_options.case_sensitive:
                    tag = tag_model.objects.get(name=tag_name)
                else:
                    tag = tag_model.objects.get(name__iexact=tag_name)
            except tag_model.DoesNotExist:
                tag = tag_model.objects.create(name=tag_name, protected=False)
            
            # Add the tag to this
            self.add(tag)
    
    set_tag_list.alters_data = True
    
    def __unicode__(self):
        """
        If called on an instance, return the tag string
        """
        if hasattr(self, 'instance'):
            return self.get_tag_string()
        else:
            return super(RelatedManagerTagMixin, self).__str__()
            
    def __str__(self):
        return unicode(self).encode('utf-8')


#
# TagField and SingleTagField
#

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
                raise ValueError("Invalid argument '%s' for TagField" % forbidden)
        
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
           
    def get_manager_name(self):
        """
        Get the field name for the SingleTagManager
        """
        return "_%s_tagulous" % self.name

        
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
     
     
#
# South migrations
#
try:
    from south import modelsinspector
    
    # Monkey-patch South to use TagModel as the base class for tag models
    # This will allow Tagulous to work in data migrations
    old_get_model_meta = modelsinspector.get_model_meta
    def get_model_meta(model):
        meta_def = old_get_model_meta(model)
        if isinstance(getattr(model, 'tag_options', None), TagOptions):
            meta_def['_bases'] = ['tagulous.models.BaseTagModel']
        return meta_def
    modelsinspector.get_model_meta = get_model_meta
    
    
    # Build keyword arguments for south
    south_kwargs = {
        # Don't want the tag model if it is generated automatically
        #'tag_model':    ['tag_model', {'ignore_if': 'auto_tag_model'}],
        
        # Never want
        #'to':           ['south_supression', {'ignore_if': 'south_supression'}],
        
        # Never want fk
        'to_field':     ['south_supression', {'ignore_if': 'south_supression'}],
        'rel_class':    ['south_supression', {'ignore_if': 'south_supression'}],
        
        # Never want m2m
        'db_table':     ['south_supression', {'ignore_if': 'south_supression'}],
        'through':      ['south_supression', {'ignore_if': 'south_supression'}],
        'symmetrical':  ['south_supression', {'ignore_if': 'south_supression'}],
    }
    
    # Add tag options
    for key, value in constants.OPTION_DEFAULTS.items():
        seek = key
        if key == 'initial':
            seek = 'initial_string'
        south_kwargs[key] = ['tag_options.%s' % seek, {'default':value}]
    
    # Add introspection rule for TagField
    modelsinspector.add_introspection_rules([
        (
            [TagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.TagField"])
    
    # No max_count for SingleTagField
    del(south_kwargs['max_count'])
    modelsinspector.add_introspection_rules([
        (
            [SingleTagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.SingleTagField"])
    
except ImportError, e:
    # South not installed
    pass
