"""
Extensions for serializers to add tag field support
"""

from ..models.fields import SingleTagField, TagField
from ..models.tagged import TaggedModel


class SerializerMixin(object):
    """
    Mixin for any Serializer which doesn't define its own handle_fk_field or
    handle_m2m_field, to add tag support
    """

    def handle_fk_field(self, obj, field):
        if isinstance(field, SingleTagField):
            self._current[field.name] = str(getattr(obj, field.name))
        else:
            super(SerializerMixin, self).handle_fk_field(obj, field)

    def handle_m2m_field(self, obj, field):
        if isinstance(field, TagField):
            self._current[field.name] = [
                tag.name for tag in getattr(obj, field.name).all()
            ]
        else:
            super(SerializerMixin, self).handle_m2m_field(obj, field)


def _deserialize_obj(obj):
    """
    Given a DeserializationObject, deserialise any tag fields
    """
    # Convert any tag fields from m2m to string assignments
    Model = obj.object.__class__
    if hasattr(Model, "_retag_to_original"):
        obj.object = obj.object._retag_to_original()
    return obj


def DeserializerWrapper(deserializer, doc=None):
    """
    Adds tag support to any deserializer which yields DeserializedObjects

    Given a deserializer, it modifies the DeserializedObjects which would
    normally be returned so tag fields are deserialized correctly.
    """

    def wrapper(object_list, **options):
        # Call normal deserializer, get generator of DeserializedObjects
        obj_generator = deserializer(object_list, **options)
        for obj in obj_generator:
            yield _deserialize_obj(obj)

    if doc:
        wrapper.__doc__ = doc
    return wrapper


def monkeypatch_get_model(serializer):
    """
    Given a model identifier, get the model - unless it's a TaggedModel, in
    which case return a temporary fake model to get it serialized.
    """
    # Django 5.2+ moved _get_model to Deserializer._get_model_from_node
    if hasattr(serializer, 'Deserializer') and hasattr(serializer.Deserializer, '_get_model_from_node'):
        old_get_model = serializer.Deserializer._get_model_from_node
    elif hasattr(serializer, '_get_model'):
        old_get_model = serializer._get_model
    else:
        # Fallback - try to find any get_model method
        if hasattr(serializer, 'get_model'):
            old_get_model = serializer.get_model
        else:
            # If we can't find any get_model method, skip monkeypatching
            return

    def _get_model(model_identifier):
        RealModel = old_get_model(model_identifier)

        if issubclass(RealModel, TaggedModel):
            Model = RealModel._detag_to_serializable()
        else:
            Model = RealModel

        return Model

    # Apply the monkeypatch to the appropriate location
    if hasattr(serializer, 'Deserializer') and hasattr(serializer.Deserializer, '_get_model_from_node'):
        serializer.Deserializer._get_model_from_node = staticmethod(_get_model)
    elif hasattr(serializer, '_get_model'):
        serializer._get_model = _get_model
    elif hasattr(serializer, 'get_model'):
        serializer.get_model = _get_model
