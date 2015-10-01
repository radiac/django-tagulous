"""
Tagulous model field descriptors

When a model has a SingleTagField or TagField, they are replaced with these
descriptors during the ``contribute_to_class`` phase.

Their main purposes is to act as getter/setters and pass data to and from
manager instances.
"""
from __future__ import unicode_literals
import collections

import django
from django.db import models
from django.utils import six

from tagulous.models.managers import (
    SingleTagManager, TagRelatedManagerMixin, FakeTagRelatedManager
)


###############################################################################
####### Base class for tag field descriptors
###############################################################################

class BaseTagDescriptor(object):
    """
    Base TagDescriptor class
    """
    def __init__(self, descriptor):
        # Store original FK/M2M descriptor and tag options
        self.descriptor = descriptor
        
        # Copy descriptor attributes
        for key, val in descriptor.__dict__.items():
            setattr(self, key, val)
    
    # If the field was created using a string, the field's tag model and
    # tag options will not be available when the descriptor is created, so
    # cannot store them directly here
    def _get_tag_model(self):
        if django.VERSION < (1, 9):
            return self.field.remote_field.to
        return self.field.remote_field.model
    tag_model = property(_get_tag_model)
    tag_options = property(lambda self: self.field.tag_options)
    
    def load_initial(self):
        """
        Load initial tags
        Be prepared to receive a DatabaseError if the model has not been synced
        """
        for tag_name in self.tag_options.initial:
            self.tag_model.objects.get_or_create(name=tag_name, defaults={
                'protected': self.tag_options.protect_initial,
            })

    def formfield(self, *args, **kwargs):
        """
        Shortcut to access formfield
        """
        return self.descriptor.field.formfield(*args, **kwargs)
        


###############################################################################
####### Descriptor for SingleTagField
###############################################################################

class SingleTagDescriptor(BaseTagDescriptor):
    """
    Descriptor to set the tag string rather than a Tag object
    Wraps the ReverseSingleRelatedObjectDescriptor and passes set and get
    requests through to the SingleTagManager
    """
    def __init__(self, descriptor):
        super(SingleTagDescriptor, self).__init__(descriptor)
        
        # The manager needs to know when the model is about to be saved
        # so that it can ensure the tag exists and assign its pk to field_id
        def pre_save_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.pre_save_handler()
        models.signals.pre_save.connect(
            pre_save_handler, sender=self.field.model, weak=False
        )
        
        # The manager needs to know after the model has been saved, so it can
        # change tag count
        def post_save_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.post_save_handler()
            
            # If raw is set, data is being injected into the system, most
            # likely from a deserialization operation. If the tag model has
            # just been deserialized too, the tag counts will probably be off.
            if kwargs.get('raw', False):
                manager.get().update_count()
            
        models.signals.post_save.connect(
            post_save_handler, sender=self.field.model, weak=False
        )
        
        # Update tag count on delete
        def post_delete_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.post_delete_handler()
        models.signals.post_delete.connect(
            post_delete_handler, sender=self.field.model, weak=False
        )
        
    def __set__(self, instance, value):
        # Check we've actually got an instance. No practical way this could
        # happen, but Django does it, so we will too
        if instance is None: # pragma: no cover
            raise AttributeError("Manager must be accessed via instance")
        
        # Otherwise set on the manager
        manager = self.get_manager(instance)
        manager.set(value)
        
    def get_manager(self, instance, instance_type=None):
        """
        Get the Manager instance for this field on this model instance.
        
        Descriptor is instantiated once per class, so we bind the Manager to
        the instance and collect it again when needed.
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
        manager = self.get_manager(instance, instance_type)
        return manager.get()
        
        
###############################################################################
####### Descriptor for TagField
###############################################################################

class TagDescriptor(BaseTagDescriptor):
    """
    Descriptor to add tag functions to the RelatedManager
    The ManyToManyField will create a ReverseManyRelatedObjectsDescriptor
    This will use a RelatedManager which we cannot customise
    This will intercept calls for the RelatedManager, and add the tag functions
    """
    def __init__(self, descriptor):
        super(TagDescriptor, self).__init__(descriptor)
        
        # After an instance is saved, save any tag changes
        def post_save_handler(sender, instance, **kwargs):
            """
            Save any tag changes
            """
            manager = self.__get__(instance)
            manager.save()
            
            # If raw is set, data is being injected into the system, most
            # likely from a deserialization operation. If the tag model has
            # just been deserialized too, the tag counts will probably be off.
            if kwargs.get('raw', False):
                for tag in manager.tags:
                    tag.update_count()
                
        models.signals.post_save.connect(
            post_save_handler, sender=self.field.model, weak=False
        )
        
        # When deleting an instance, Django does not call the add/remove of the
        # M2M manager, so tag counts would be too high. Related to:
        #   https://code.djangoproject.com/ticket/6707
        # We need to clear the M2M manually to update tag counts
        def pre_delete_handler(sender, instance, **kwargs):
            """
            Safely clear the M2M tag field, persisting tags on the manager
            """
            # Get the manager and tell it to clear
            manager = self.__get__(instance)
            
            # Get tags so we can make them available to the fake manager later
            manager.reload()
            tags = manager.tags
            
            # Clear the object
            manager.clear()
            
            # Put the tags back on the manager
            manager.tags = tags
        models.signals.pre_delete.connect(
            pre_delete_handler, sender=self.field.model, weak=False
        )
        
    def get_manager(self, instance, instance_type=None):
        """
        Get the Manager instance for this field on this model instance.
        
        Descriptor is instantiated once per class, so we bind the Manager to
        the instance and collect it again when needed.
        
        While the instance is not saved (does not have a pk), a fake manager
        is used to hold unsaved tags; database methods are disallowed.
        """
        # Get existing mamager
        attname = self.descriptor.field.get_manager_name()
        manager = getattr(instance, attname, None)
        manager_type = self.descriptor.related_manager_cls
        
        # Find which manager we should be using
        if instance.pk:
            # Can use real manager
            if isinstance(manager, FakeTagRelatedManager):
                # Convert fake manager to real manager
                fake_manager = manager
                manager = self.create_manager(instance, instance_type)
                manager.load_from_tagmanager(fake_manager)
                
            elif manager is None:
                # Create real manager
                manager = self.create_manager(instance, instance_type)
                
            # Otherwise already have real manager
        else:
            # Have to use the fake one
            if isinstance(manager, manager_type):
                # Was using a real manager, but instance must have been deleted
                real_manager = manager
                manager = FakeTagRelatedManager(self, instance, instance_type)
                manager.load_from_tagmanager(real_manager)
            
            elif manager is None:
                # Create fake manager
                manager = FakeTagRelatedManager(self, instance, instance_type)
            
            # Otherwise already have a fake manager
        
        # Set it in case it changed
        setattr(instance, attname, manager)
        return manager
    
    def create_manager(self, instance, instance_type):
        # Get the RelatedManager that should have been returned
        manager = self.descriptor.__get__(instance, instance_type)
        
        # Add in the mixin
        manager.__class__ = type(
            str('TagRelatedManager'),
            (TagRelatedManagerMixin, manager.__class__),
            {}
        )
        
        # Manager is already instantiated; initialise tagulous in it
        manager.init_tagulous(self)
        
        return manager
    
    def __get__(self, instance, instance_type=None):
        # If no instance, return self
        if not instance:
            return self
        
        # Otherwise get from the manager
        manager = self.get_manager(instance, instance_type)
        return manager
        
    def __set__(self, instance, value):
        # Check we've actually got an instance. No practical way this could
        # happen, but Django does it, so we will too
        if instance is None: # pragma: no cover
            raise AttributeError("Manager must be accessed via instance")
        
        # Get the manager
        manager = self.__get__(instance)
        
        # Set value
        if not value:
            # Clear
            manager.set_tag_string('')
        
        elif isinstance(value, six.string_types):
            # If it's a string, it must be a tag string
            manager.set_tag_string(value)
        
        elif isinstance(value, collections.Iterable):
            # An iterable goes in as a list of things that are, or can be
            # converted to, strings
            manager.set_tag_list(value)
            
        else:
            # Unknown
            raise ValueError('Unexpected value assigned to TagField')
