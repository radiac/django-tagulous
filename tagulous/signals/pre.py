"""
Signals registered before models are loaded

These are registered as part of Tagulous model initialisation, so apps following this in
INSTALLED_APPS can have their models enhanced.
"""

from django.db.models.signals import class_prepared

from .. import settings
from ..models.tagged import TaggedModel


def class_prepared_listener(sender, **kwargs):
    """
    Listen to the class_prepared signal and subclass any model with tag
    fields
    """
    TaggedModel.cast_class(sender)


def register_pre_signals():
    """
    Called from tagulous/models/__init__.py
    """
    if settings.ENHANCE_MODELS:
        class_prepared.connect(class_prepared_listener, weak=False)
