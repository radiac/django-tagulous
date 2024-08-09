"""
Tagulous model field descriptors

When a model has a SingleTagField or TagField, they are replaced with these
descriptors during the ``contribute_to_class`` phase.

Their main purposes is to act as getter/setters and pass data to and from
manager instances.
"""

from collections.abc import Iterable

from django.db.models import Q

from .managers import FakeTagRelatedManager, SingleTagManager, TagRelatedManagerMixin

# ##############################################################################
# ###### Base class for tag field descriptors
# ##############################################################################


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
    tag_model = property(lambda self: self.field.remote_field.model)
    tag_options = property(lambda self: self.field.tag_options)

    def load_initial(self):
        """
        Load initial tags
        Be prepared to receive a DatabaseError if the model has not been synced
        """
        for tag_name in self.tag_options.initial:
            self.tag_model.objects.get_or_create(
                name=tag_name, defaults={"protected": self.tag_options.protect_initial}
            )

    def formfield(self, *args, **kwargs):
        """
        Shortcut to access formfield
        """
        return self.descriptor.field.formfield(*args, **kwargs)


# ##############################################################################
# ###### Descriptor for SingleTagField
# ##############################################################################


class SingleTagDescriptor(BaseTagDescriptor):
    """
    Descriptor to set the tag string rather than a Tag object
    Wraps the ReverseSingleRelatedObjectDescriptor and passes set and get
    requests through to the SingleTagManager
    """

    def __set__(self, instance, value):
        # Check we've actually got an instance. No practical way this could
        # happen, but Django does it, so we will too
        if instance is None:  # pragma: no cover
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
        related = manager.get()

        if not related:
            return related

        # Add get_similar_objects()
        field = self.field

        def get_similar_objects():
            # Start with all objects except the source object
            qs = field.model.objects.exclude(pk=instance.pk)

            # Find ones which match
            qs = qs.filter(Q(**{f"{field.name}": getattr(instance, field.name)}))

            return qs

        related.get_similar_objects = get_similar_objects

        return related


# ##############################################################################
# ###### Descriptor for TagField
# ##############################################################################


class TagDescriptor(BaseTagDescriptor):
    """
    Descriptor to add tag functions to the RelatedManager
    The ManyToManyField will create a ReverseManyRelatedObjectsDescriptor
    This will use a RelatedManager which we cannot customise
    This will intercept calls for the RelatedManager, and add the tag functions
    """

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
            str("TagRelatedManager"), (TagRelatedManagerMixin, manager.__class__), {}
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
        if instance is None:  # pragma: no cover
            raise AttributeError("Manager must be accessed via instance")

        # Get the manager
        manager = self.__get__(instance)

        # Set value
        if not value:
            # Clear
            manager.set_tag_string("")

        elif isinstance(value, str):
            # If it's a string, it must be a tag string
            manager.set_tag_string(value)

        elif isinstance(value, Iterable):
            # An iterable goes in as a list of things that are, or can be
            # converted to, strings
            manager.set_tag_list(value)

        else:
            # Unknown
            raise ValueError("Unexpected value assigned to TagField")

    @property
    def through(self):
        return self.descriptor.through
