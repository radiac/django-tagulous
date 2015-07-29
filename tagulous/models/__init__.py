"""
Tagulous models

Make important functions and classes available on tagulous.models
"""
from tagulous.models.options import TagOptions
from tagulous.models.models import (
    BaseTagModel, TagModel, BaseTagTreeModel, TagTreeModel,
    TagModelQuerySet, TagModelManager,
)
from tagulous.models.managers import (
    SingleTagManager, TagRelatedManagerMixin,
)
from tagulous.models.descriptors import (
    BaseTagDescriptor, SingleTagDescriptor, TagDescriptor,
)
from tagulous.models.fields import (
    BaseTagField, SingleTagField, TagField,
    singletagfields_from_model, tagfields_from_model,
)

from tagulous.models import initial
from tagulous.models import migrations
from tagulous.models.tagged import TaggedModel, TaggedManager, TaggedQuerySet
