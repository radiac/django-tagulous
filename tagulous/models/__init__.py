"""
Tagulous models

Make important functions and classes available on tagulous.models
"""

from tagulous.models.options import TagOptions
from tagulous.models.models import BaseTagModel, TagModel
from tagulous.models.managers import (
    BaseTagManager, SingleTagManager, RelatedManagerTagMixin,
)
from tagulous.models.descriptors import (
    BaseTagDescriptor, SingleTagDescriptor, TagDescriptor,
)
from tagulous.models.fields import (
    BaseTagField, SingleTagField, TagField
)

from tagulous.models import queryset
from tagulous.models import initial
from tagulous.models import migrations



