"""
Tagulous models

Make important functions and classes available on tagulous.models
"""

from ..signals.pre import register_pre_signals
from . import initial, migrations  # noqa
from .descriptors import BaseTagDescriptor, SingleTagDescriptor, TagDescriptor  # noqa
from .fields import (  # noqa
    BaseTagField,
    SingleTagField,
    TagField,
    singletagfields_from_model,
    tagfields_from_model,
)
from .managers import SingleTagManager, TagRelatedManagerMixin  # noqa
from .models import (  # noqa
    BaseTagModel,
    BaseTagTreeModel,
    TagModel,
    TagModelManager,
    TagModelQuerySet,
    TagTreeModel,
)
from .options import TagOptions  # noqa
from .tagged import TaggedManager, TaggedModel, TaggedQuerySet  # noqa

register_pre_signals()
