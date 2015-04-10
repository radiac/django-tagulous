"""
Tagulous model field descriptors

When a model has a SingleTagField or TagField, they are replaced with these
descriptors during the ``contribute_to_class`` phase.

Their main purposes is to act as getter/setters and pass data to and from
manager instances.
"""

from django.db import models

from tagulous.models.managers import SingleTagManager, RelatedManagerTagMixin


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
        # decrement the old tag without risk of cascading the delete if count=0
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
        manager.tag_model = self.tag_model
        
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
