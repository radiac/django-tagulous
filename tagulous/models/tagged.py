"""
Tagulous extensions for models which use tag fields (tagged models)

These are all applied automatically when the TAGULOUS_ENHANCE_MODELS setting
is enabled.
"""

import copy

import django
from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction

from .. import utils
from ..constants import TAGGED_ATTR_MANAGER
from .cast import cast_instance
from .fields import (
    BaseTagField,
    SingleTagField,
    TagField,
    singletagfields_from_model,
    tagfields_from_model,
)


def _split_kwargs(model, kwargs, lookups=False, with_fields=False):
    """
    Split kwargs into fields which are safe to pass to create, and
    m2m tag fields, creating SingleTagFields as required.

    If lookups is True, TagFields with tagulous-specific lookups will also be
    matched, and the returned tag_fields will be a dict of tuples in the
    format ``(val, lookup)``

    The only tagulous-specific lookup is __exact

    For internal use only - likely to change significantly in future versions

    Returns a tuple of safe_fields, singletag_fields, tag_fields

    If with_fields is True, a fourth argument will be returned - a dict to
    look up Field objects from their names
    """
    safe_fields = {}
    singletag_fields = {}
    tag_fields = {}
    field_lookup = {}
    for field_name, val in kwargs.items():
        # Check for lookup
        if lookups and "__" in field_name:
            orig_field_name = field_name
            field_name, lookup = field_name.split("__", 1)

            # Only one known lookup
            if lookup == "exact":
                try:
                    field = model._meta.get_field(field_name)
                except FieldDoesNotExist:
                    # Unknown - pass it on untouched
                    pass
                else:
                    if isinstance(field, TagField):
                        # Store for later
                        tag_fields[field_name] = (val, lookup)
                        field_lookup[field_name] = field
                        continue

            # Irrelevant lookup - no need to take special actions
            safe_fields[orig_field_name] = val
            continue

        # No lookup
        # Try to look up the field
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            # Assume it's something clever and pass it through untouched
            # If it's invalid, an error will be raised later anyway
            safe_fields[field_name] = val

            # Next field
            continue

        field_lookup[field_name] = field
        # Take special measures depending on field type
        if isinstance(field, SingleTagField):
            singletag_fields[field_name] = val

        elif isinstance(field, TagField):
            # Store for later
            if lookups:
                tag_fields[field_name] = (val, None)
            else:
                tag_fields[field_name] = val

        else:
            safe_fields[field_name] = val

    if with_fields:
        return safe_fields, singletag_fields, tag_fields, field_lookup

    return safe_fields, singletag_fields, tag_fields


# ##############################################################################
# ############################################################## TaggedQuerySet
# ##############################################################################


class TaggedQuerySet(models.query.QuerySet):
    """
    A QuerySet with support for Tagulous tag fields
    """

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Custom lookups for tag fields
        """
        if django.VERSION >= (3, 2):
            # Arguments changed to _filter_or_exclude(self, negate, args, kwargs)
            if len(args) == 2:
                args, kwargs = args
            elif set(kwargs.keys()) == {"args", "kwargs"}:
                args, kwargs = kwargs["args"], kwargs["kwargs"]

        # TODO: Replace with custom lookups
        safe_fields, singletag_fields, tag_fields, field_lookup = _split_kwargs(
            self.model, kwargs, lookups=True, with_fields=True
        )

        # Look up string values for SingleTagFields by name
        for field_name, val in singletag_fields.items():
            query_field_name = field_name
            if isinstance(val, str):
                query_field_name += "__name"
                if not field_lookup[field_name].tag_options.case_sensitive:
                    query_field_name += "__iexact"
            safe_fields[query_field_name] = val

        # Query as normal
        if django.VERSION >= (3, 2):
            qs = super(TaggedQuerySet, self)._filter_or_exclude(
                negate, args, safe_fields
            )
        else:
            qs = super(TaggedQuerySet, self)._filter_or_exclude(
                negate, *args, **safe_fields
            )

        # Look up TagFields by string name
        #
        # Each of these comparisons will be done with a subquery; for
        # A filter can chain, ie .filter(tags__name=..).filter(tags__name=..),
        # but exclude won't work that way; has to be done with a subquery
        for field_name, val in tag_fields.items():
            val, lookup = val
            tag_options = field_lookup[field_name].tag_options

            # Only perform custom lookup if value is a string
            if not isinstance(val, str):
                if django.VERSION >= (3, 2):
                    qs = super(TaggedQuerySet, self)._filter_or_exclude(
                        negate, [], {field_name: val}
                    )
                else:
                    qs = super(TaggedQuerySet, self)._filter_or_exclude(
                        negate, **{field_name: val}
                    )
                continue

            # Parse the tag string
            tags = utils.parse_tags(val, space_delimiter=tag_options.space_delimiter)

            # Prep the subquery
            subqs = qs
            if negate:
                subqs = self.__class__(model=self.model, using=self._db)

            # To get an exact match, filter this queryset to only include
            # items with a tag count that matches the number of specified tags
            if lookup == "exact":
                count_name = "_tagulous_count_%s" % field_name
                subqs = subqs.annotate(**{count_name: models.Count(field_name)}).filter(
                    **{count_name: len(tags)}
                )
                # Explicit order as meta ordering will be ignored
                subqs = subqs.order_by("name")

            # Prep the field name
            query_field_name = field_name + "__name"
            if not tag_options.case_sensitive:
                query_field_name += "__iexact"

            # Now chain the filters for each tag
            #
            # Have to do it this way to create new inner joins for each tag;
            # ANDing Q objects will do it all on a single inner join, which
            # will match nothing
            for tag in tags:
                subqs = subqs.filter(**{query_field_name: tag})

            # Fold subquery back into main query
            if negate:
                # Exclude on matched ID
                qs = qs.exclude(pk__in=subqs.values("pk"))
            else:
                # A filter op can just replace the main query
                qs = subqs

        return qs

    def create(self, **kwargs):
        # Create object as normal
        safe_fields, singletag_fields, tag_fields = _split_kwargs(self.model, kwargs)

        # Could convert SingleTagFields to instances with
        # field.tag_model.objects.get_or_create, but model constructor will
        # assign it through the descriptor anyway, so this is unnecessary.
        # SingleTagFields are safe
        safe_fields.update(singletag_fields)

        with transaction.atomic():
            # Create as normal
            obj = super(TaggedQuerySet, self).create(**safe_fields)

            # Add tag fields
            for field_name, val in tag_fields.items():
                setattr(obj, field_name, val)
                getattr(obj, field_name).save()

            return obj

    def get_or_create(self, defaults=None, **kwargs):
        # Get or create object as normal
        safe_fields, singletag_fields, tag_fields = _split_kwargs(self.model, kwargs)

        # As in .create, SingleTagFields are ok to create
        # Existing .get will be fine for lookup
        safe_fields.update(singletag_fields)

        # Use normal get_or_create if there are no tag fields
        if len(tag_fields) == 0:
            return super(TaggedQuerySet, self).get_or_create(defaults, **safe_fields)

        # Try to find it using get - that is able to handle tag_fields
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

    @classmethod
    def cast_class(cls, queryset):
        """
        Changes the class of the specified queryset to a subclass of TaggedQuerySet
        and the original class, so it has all the same properties it did when it
        was first initialised, but is now a TaggedQuerySet subclass.

        The new class is given the same name as the old class, but with the prefix
        CAST_CLASS_PREFIX to indicate the type of the object has changed, eg a normal
        QuerySet will become TagulousCastTaggedQuerySet.
        """
        cast_instance(queryset, cls)
        return queryset

    def similarly_tagged(self, instance, field_name):
        """
        Filter the queryset to objects which are similarly tagged to the specified model
        instance.

        Arguments:
            instance    Instance of the model whose tags we're comparing to
            field_name  Name of TagField where we're checking similarity
        """
        # Start with a queryset of the tagged model, excluding the instance
        qs = self.exclude(pk=instance.pk)

        # Annotate with count of similarly tagged
        q_filter = {f"{field_name}__in": getattr(instance, field_name).all()}
        similar = qs.annotate(
            tagulous_similarity=models.Count(
                field_name,
                models.Q(**q_filter),
                distinct=True,
            )
        )

        # Exclude any zero matches
        similar = similar.exclude(tagulous_similarity=0)

        # Order by similarity with most similar first
        ordering = ["-tagulous_similarity"] + list(similar.model._meta.ordering)
        similar = similar.order_by(*ordering)

        return similar


# ##############################################################################
# ############################################################## TaggedManager
# ##############################################################################


class TaggedManager(models.Manager):
    """
    A manager with support for Tagulous tag fields
    """

    # The class of a tag-enabled queryset. Here so a custom TaggedManager can
    # replace it with a custom TaggedQuerySet subclass.
    tagulous_queryset = TaggedQuerySet

    def _enhance_queryset(self, qs):
        """
        Enhance an existing queryset with the class in self.tagulous_queryset
        """
        return self.tagulous_queryset.cast_class(qs)

    def get_queryset(self, *args, **kwargs):
        """
        Get the original queryset and then enhance it
        """
        qs = super(TaggedManager, self).get_queryset(*args, **kwargs)
        return self._enhance_queryset(qs)

    @classmethod
    def cast_class(cls, manager):
        """
        Changes the class of the specified manager to a subclass of TaggedManager
        and the original class, so it has all the same properties it did when it
        was first initialised, but is now a TaggedManager subclass.

        The new class is given the same name as the old class, but with the prefix
        CAST_CLASS_PREFIX to indicate the type of the object has changed, eg a normal
        Manager will become TagulousCastTaggedManager
        """
        cast_instance(manager, cls)
        return manager

    def similarly_tagged(self, instance, field_name):
        return self.get_queryset().similarly_tagged(instance, field_name)


# ##############################################################################
# ############################################################## TaggedModel
# ##############################################################################


class TaggedModel(models.Model):
    """
    An abstract model base class with support for Tagulous tag fields
    """

    def __init__(self, *args, **kwargs):
        safe_fields, singletag_fields, tag_fields = _split_kwargs(self, kwargs)

        # Constructor has always been happy with ForeignKeys
        safe_fields.update(singletag_fields)

        # Call old init
        super(TaggedModel, self).__init__(*args, **safe_fields)

        # Add on TagField values
        for field_name, val in tag_fields.items():
            setattr(self, field_name, val)

    def __getstate__(self):
        """
        Pickle tag fields
        """
        state = super().__getstate__()

        for field in self._meta.get_fields():
            if isinstance(field, BaseTagField):
                # Remove manager from state
                attr = TAGGED_ATTR_MANAGER % field.name
                if attr in state:
                    del state[attr]

        return state

    @classmethod
    def cast_class(cls, model):
        """
        If the model contains tag fields, change the model to subclass
        TaggedModel and enhance its managers. Called automatically on all
        models with tag fields when settings.ENHANCE_MODELS is True.

        Arguments:
            model   The model to turn into a TaggedModel subclass.
                    Will only be changed if it has tag fields.
        """
        # See if there are tag fields on this model
        tag_fields = singletagfields_from_model(model) + tagfields_from_model(model)

        # If there are no tag fields skip
        if not tag_fields:
            return

        # Ensure the model subclasses TaggedModel
        if not issubclass(model, TaggedModel):
            model.__bases__ = (TaggedModel,) + model.__bases__

        # Ensure the manager subclasses TaggedManager
        if hasattr(model, "objects") and not issubclass(
            model.objects.__class__, TaggedManager
        ):
            TaggedManager.cast_class(model.objects)

        return model

    @classmethod
    def _detag_to_serializable(cls):
        """
        Clone a fake version of this model, replacing tag fields with Field
        objects, because their to_python method will not modify arguments.

        Used by serializers to pass list values for tag fields through the
        python serializer, to be loaded back into the real tagged model when
        safe.
        """
        # Get fields on this model
        fields = cls._meta.get_fields()

        # Create a fake model
        class FakeTaggedModel(models.Model):
            def __init__(self, *args, **kwargs):
                # Django 3.2 introduced a TypeError when trying to instantiate an
                # abstract model. Set it to False to get past the check.
                if django.VERSION >= (3, 2):
                    self._meta.abstract = False

                super().__init__(*args, **kwargs)

                if django.VERSION >= (3, 2):
                    self._meta.abstract = True

            def _retag_to_original(self):
                """
                Convert this instance into an instance of the proper class it
                should have been, before _detag_to_serializable converted it.
                """
                # cls and fields from closure's scope
                data = {}
                for field in fields:
                    # ManyToOneRel and ManyToManyRel objects have no attribute
                    # contribute_to_class
                    if isinstance(field, (models.ManyToOneRel, models.ManyToManyRel)):
                        continue
                    # Find fields which are either TagFields, or not M2Ms -
                    # anything which Deserializer will have stored data for
                    elif isinstance(field, TagField) or not (
                        field.remote_field
                        and isinstance(field.remote_field, models.ManyToManyRel)
                    ):
                        # Get data from object
                        data[field.name] = getattr(self, field.name)
                return cls(**data)

            class Meta:
                abstract = True

        # Add fields to fake model
        for field in fields:
            if isinstance(field, (models.ManyToOneRel, models.ManyToManyRel)):
                # ManyToOneRel and ManyToManyRel objects have no attribute
                # contribute_to_class
                continue

            elif isinstance(field, BaseTagField):
                clone_field = models.Field(blank=field.blank, null=field.null)

            else:
                clone_field = copy.deepcopy(field)

            clone_field.contribute_to_class(FakeTaggedModel, field.name)

        FakeTaggedModel._tagulous_original_cls = cls
        return FakeTaggedModel

    class Meta:
        abstract = True
