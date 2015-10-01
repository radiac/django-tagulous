"""
JSON serializer with Tagulous support
"""
from __future__ import unicode_literals

from django.core.serializers import json as json_serializer
from django.utils import six

from tagulous.serializers import base


class Serializer(base.SerializerMixin, json_serializer.Serializer):
    """
    JSON serializer with tag field support
    """
    pass


Deserializer = base.DeserializerWrapper(
    json_serializer.Deserializer,
    doc="Deserialize a stream or string of JSON data, with tag field support",
)
