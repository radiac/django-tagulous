"""
XML serializer with Tagulous support
"""
from __future__ import unicode_literals

from django.core.serializers import xml_serializer
from django.utils import six

from tagulous.models.fields import SingleTagField, TagField
from tagulous.models.tagged import TaggedModel

from tagulous.serializers import base


class FakeObject(object):
    """
    Fake object to feed into the standard XML serializer, to trick it into
    serializing a tag field as a text field
    """
    def __init__(self, field_name, value):
        setattr(self, field_name, value)
        self.value = value
    
class FakeField(object):
    """
    Fake field to feed into the standard XML serializer, to trick it into
    serializing a tag field as a text field
    """
    def __init__(self, name):
        self.name = name
    get_internal_type = lambda self: 'TextField'
    value_to_string = lambda self, obj: obj.value
    

class Serializer(xml_serializer.Serializer):
    """
    XML serializer with tag field support
    """
    def handle_tagfield(self, obj, field):
        """
        Trick XML serializer into serializing this as text
        """
        tag_string = six.text_type(getattr(obj, field.name))
        fake_obj = FakeObject(field.name, tag_string)
        fake_field = FakeField(field.name)
        self.handle_field(fake_obj, fake_field)
        
    def handle_fk_field(self, obj, field):
        if isinstance(field, SingleTagField):
            self.handle_tagfield(obj, field)
        else:
            super(Serializer, self).handle_fk_field(obj, field)

    def handle_m2m_field(self, obj, field):
        if isinstance(field, TagField):
            self.handle_tagfield(obj, field)
        else:
            super(Serializer, self).handle_m2m_field(obj, field)


class Deserializer(xml_serializer.Deserializer):
    def _handle_object(self, node):
        obj = super(Deserializer, self)._handle_object(node)
        return base._deserialize_obj(obj)
    
    # Could override _handle_fk_field_node and _handle_m2m_field_node with
    # code to check for tag fields, but the code to turn them into fake
    # textfields is already in place
    
    def _get_model_from_node(self, node, attr):
        RealModel = super(Deserializer, self)._get_model_from_node(node, attr)
        
        if issubclass(RealModel, TaggedModel):
            Model = RealModel._detag_to_serializable()
        else:
            Model = RealModel
        
        return Model
