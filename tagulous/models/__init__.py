"""
Tagulous models

Make important functions and classes available on tagulous.models
"""
from tagulous.models import signals  # NOQA
from tagulous.models import initial, migrations
from tagulous.models.descriptors import (
    BaseTagDescriptor,
    SingleTagDescriptor,
    TagDescriptor,
)
from tagulous.models.fields import (
    BaseTagField,
    SingleTagField,
    TagField,
    singletagfields_from_model,
    tagfields_from_model,
)
from tagulous.models.managers import SingleTagManager, TagRelatedManagerMixin
from tagulous.models.models import (
    BaseTagModel,
    BaseTagTreeModel,
    TagModel,
    TagModelManager,
    TagModelQuerySet,
    TagTreeModel,
)
from tagulous.models.options import TagOptions
from tagulous.models.tagged import TaggedManager, TaggedModel, TaggedQuerySet
