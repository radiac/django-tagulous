from rest_framework import serializers
from rest_framework.fields import CharField, ListField

from ..models.fields import SingleTagField, TagField


class TagRelatedManagerField(ListField):
    """
    Serialize a TagField to a list of strings
    """

    def __init__(self, *args, **kwargs):
        """
        Default the child to a CharField
        """
        kwargs.setdefault("child", CharField(required=kwargs.get("required", False)))
        super().__init__(*args, **kwargs)

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [
            self.child.to_representation(item) if item is not None else None
            for item in data.all()
        ]


class TagSerializer(serializers.ModelSerializer):
    """
    Serialize tag fields as strings
    """

    def get_fields(self):
        """
        Override field mappings to use string string serializers for tag fields
        """
        field_mappings = super().get_fields()

        fields = self.Meta.model._meta.get_fields()
        for field in fields:
            if field.name not in field_mappings:
                continue

            if isinstance(field, SingleTagField):
                field_mappings[field.name] = CharField(required=field.required)
            elif isinstance(field, TagField):
                # M2M cannot have required=True
                field_mappings[field.name] = TagRelatedManagerField(required=False)

        return field_mappings
