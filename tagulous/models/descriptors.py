"""
Tagulous model field descriptors

When a model has a SingleTagField or TagField, they are replaced with these
descriptors during the ``contribute_to_class`` phase.

Their main purposes is to act as getter/setters and pass data to and from
manager instances.
"""

import collections

from django.db import models

from tagulous.models.managers import SingleTagManager, RelatedManagerTagMixin


###############################################################################
####### Base class for tag field descriptors
###############################################################################

class BaseTagDescriptor(object):
    """
    Base TagDescriptor class
    """
    def __init__(self, descriptor, tag_options):
        # Store original FK/M2M descriptor and tag options
        self.descriptor = descriptor
        self.tag_options = tag_options
        
        # Copy descriptor attributes
        for key, val in descriptor.__dict__.items():
            setattr(self, key, val)
            
        # Add a convenient reference to the tag model
        self.tag_model = self.field.rel.to
        
    def load_initial(self):
        """
        Load initial tags
        Be prepared to receive a DatabaseError if the model has not been synced
        """
        for tag_name in self.tag_options.initial:
            self.tag_model.objects.get_or_create(name=tag_name, defaults={
                'protected': self.tag_options.protect_initial,
            })

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
            manager = self.create_manager(instance, instance_type)
            setattr(instance, attname, manager)
        return manager
    
    def create_manager(self, instance, instance_type):
        raise NotImplementedError('Implement in subclass')

    
###############################################################################
####### Descriptor for SingleTagField
###############################################################################

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
        models.signals.pre_save.connect(
            pre_save_handler, sender=self.field.model, weak=False
        )
        
        # The manager needs to know after the model has been saved, so it can
        # change tag count
        def post_save_handler(sender, instance, **kwargs):
            manager = self.get_manager(instance)
            manager.post_save_handler()
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
        # Check we can do this
        # descriptor.__set__() will do this again, but can't be avoided
        if instance is None:
            raise AttributeError("Manager must be accessed via instance")
        
        # Otherwise set on the manager
        manager = self.get_manager(instance)
        manager.set(value)
        
    def create_manager(self, instance, instance_type):
        return SingleTagManager(self, instance)
    
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
    def __init__(self, descriptor, tag_options):
        super(TagDescriptor, self).__init__(descriptor, tag_options)
        
        # After an instance is saved, save any tag changes
        def post_save_handler(sender, instance, **kwargs):
            """
            Save any tag changes
            """
            manager = self.__get__(instance)
            manager.save()
        models.signals.post_save.connect(
            post_save_handler, sender=self.field.model, weak=False
        )
        
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
        models.signals.pre_delete.connect(
            pre_delete_handler, sender=self.field.model, weak=False
        )
        
    def create_manager(self, instance, instance_type):
        # Get the RelatedManager that should have been returned
        manager = self.descriptor.__get__(instance, instance_type)
        
        # Add in the mixin
        manager.__class__ = type(
            'TagRelatedManager',
            (manager.__class__, RelatedManagerTagMixin),
            {}
        )
        
        # Switch add, remove and clear, keeping the old versions to call later
        manager._old_add,    manager.add    = manager.add,    manager._add
        manager._old_remove, manager.remove = manager.remove, manager._remove
        manager._old_clear,  manager.clear  = manager.clear,  manager._clear
        
        # Manager is already instantiated; initialise tagulous in it
        manager.__init_tagulous__(self)
        
        return manager
    
    def __get__(self, instance, instance_type=None):
        # If no instance, return self
        if not instance:
            return self
        
        # Otherwise get from the manager
        manager = self.get_manager(instance, instance_type)
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
            manager.set_tag_string('')
        
        elif isinstance(value, basestring):
            # If it's a string, it must be a tag string
            manager.set_tag_string(value)
        
        elif isinstance(value, RelatedManagerTagMixin):
            # A manager's tags are copied
            manager.set_tag_list(value.get_tag_list())
            
        elif isinstance(value, collections.Iterable):
            # An iterable goes in as a list of things that are, or can be
            # converted to, strings
            manager.set_tag_list(value)
            
        else:
            # Unknown
            raise ValueError('Unexpected value assigned to TagField')
