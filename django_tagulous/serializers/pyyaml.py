"""
YAML serializer with Tagulous support
"""

from django.core.serializers import pyyaml as pyyaml_serializer

from . import base


class Serializer(base.SerializerMixin, pyyaml_serializer.Serializer):
    """
    YAML serializer with tag field support
    """

    pass


Deserializer = base.DeserializerWrapper(
    pyyaml_serializer.Deserializer,
    doc="Deserialize a stream or string of YAML data, with tag field support",
)
