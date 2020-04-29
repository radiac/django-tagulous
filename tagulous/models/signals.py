"""
Model signal handlers

This really should be tagulous.signals, imported by the tagulous app's ready()
call, as per the django docs [1] - but that's only available in Django 1.7 or
later and we're supporting back to 1.4, so we'll keep it in here for now.

[1] https://docs.djangoproject.com/en/1.10/topics/signals/#connecting-receiver-functions
"""
from django.db import models

from tagulous import settings
from tagulous.models.fields import SingleTagField, TagField
from tagulous.models.tagged import TaggedModel


if settings.ENHANCE_MODELS:

    def class_prepared_listener(sender, **kwargs):
        """
        Listen to the class_prepared signal and subclass any model with tag
        fields
        """
        TaggedModel.cast_class(sender)

    models.signals.class_prepared.connect(class_prepared_listener, weak=False)


class TaggedSignalHandler(object):
    """
    Base class handling signals from TaggedModel subclasses
    """

    def __call__(self, sender, instance, **kwargs):
        if not self.is_relevant(sender):
            return

        for field, field_type in self.get_fields(sender):
            descriptor = getattr(sender, field.name)
            manager = descriptor.get_manager(instance)

            self.handle(manager, field_type, kwargs.get("raw", False))

    def is_relevant(self, sender):
        return issubclass(sender, TaggedModel)

    def get_fields(self, sender):
        """
        Generator which returns (field, field_type) pairs
        """
        for field in sender._meta.get_fields():
            if isinstance(field, SingleTagField):
                yield (field, SingleTagField)
            elif isinstance(field, TagField):
                yield (field, TagField)

    def handle(self, manager, field_type, is_raw):
        raise NotImplementedError()


class PreSaveHandler(TaggedSignalHandler):
    """
    Pre-save signal handler

    Make sure SingleTagField is in correct format to be saved. The manager needs to know
    when the model is about to be saved # so that it can ensure the tag exists and
    assign its pk to field_id.
    """

    def handle(self, manager, field_type, is_raw):
        if field_type != SingleTagField:
            return
        manager.pre_save_handler()


class PostSaveHandler(TaggedSignalHandler):
    """
    Post-save signal handler

    Ensure both tag fields' states are saved
    """

    def handle(self, manager, field_type, is_raw):
        manager.post_save_handler()

        # If raw is set, data is being injected into the system, most likely from a
        # deserialization operation. If the tag model has just been deserialized too,
        # the tag counts will probably be off.
        if is_raw:
            if field_type == SingleTagField:
                manager.get().update_count()
            else:
                for tag in manager.tags:
                    tag.update_count()


class PropagatedSignalMixin(object):
    def get_fields(self, sender):
        """
        Post delete signal propagates up the class hierarchy, so filter fields
        returned to those belonging to the model which raised this signal
        """
        for field, field_type in super(PropagatedSignalMixin, self).get_fields(sender):
            if field.model != sender:
                continue
            yield (field, field_type)


class PreDeleteHandler(PropagatedSignalMixin, TaggedSignalHandler):
    """
    Pre-delete signal handler

    Ensure TagField is cleaned out before the main object is deleted
    """

    def handle(self, manager, field_type, is_raw):
        if field_type != TagField:
            return
        manager.pre_delete_handler()


class PostDeleteHandler(PropagatedSignalMixin, TaggedSignalHandler):
    """
    Post-delete signal handler

    Update tag count on delete
    """

    def handle(self, manager, field_type, is_raw):
        if field_type != SingleTagField:
            return
        manager.post_delete_handler()


models.signals.pre_save.connect(PreSaveHandler(), weak=False)
models.signals.post_save.connect(PostSaveHandler(), weak=False)
models.signals.pre_delete.connect(PreDeleteHandler(), weak=False)
models.signals.post_delete.connect(PostDeleteHandler(), weak=False)
