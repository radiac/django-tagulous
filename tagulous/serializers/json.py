"""
JSON serializer with Tagulous support
"""

from django.core.serializers import json as json_serializer

from . import base


class Serializer(base.SerializerMixin, json_serializer.Serializer):
    """
    JSON serializer with tag field support
    """

    pass


Deserializer = base.DeserializerWrapper(
    json_serializer.Deserializer,
    doc="Deserialize a stream or string of JSON data, with tag field support",
)
