"""
Python serializer with Tagulous support
"""
from __future__ import unicode_literals

from django.core.serializers import python as python_serializer
from django.utils import six

from tagulous.serializers import base


class Serializer(base.SerializerMixin, python_serializer.Serializer):
    """
    Serializes a QuerySet to basic Python objects, with tag field support
    """
    pass
    

Deserializer = base.DeserializerWrapper(python_serializer.Deserializer, doc=(
    "Deserialize Python objects into Django ORM instances, with tag field "
    "support"
))

base.monkeypatch_get_model(python_serializer)
