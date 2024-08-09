"""
Tagulous tag models
"""

from django.db import IntegrityError, models, router, transaction
from django.db.models import F, Max
from django.db.models.functions import Floor
from django.utils.text import slugify

from .. import constants, settings, utils
from .options import TagOptions

# ##############################################################################
# ###### TagModel manager and queryset
# ##############################################################################


class TagModelQuerySet(models.query.QuerySet):
    def initial(self):
        """
        Reduce the queryset to only include initial tags left in the queryset
        """
        return self.filter(name__in=self.model.tag_options.initial)

    def filter_or_initial(self, *args, **kwargs):
        """
        Reduce the queryset to match the specified filter, but also include
        any initial tags left in the queryset.

        An example of usage would be where tags are only visible to the user
        who added them, but you also want them to see the initial default tags.
        """
        return self.filter(
            models.Q(*args, **kwargs)
            | models.Q(name__in=self.model.tag_options.initial)
        )

    def weight(self, min=settings.WEIGHT_MIN, max=settings.WEIGHT_MAX):
        """
        Add a ``weight`` integer field to objects, weighting the ``count``
        between ``min`` and ``max``.

        Suitable for use with a tag cloud
        """
        # Ignoring PEP 8 intentionally regarding conflict of min/max keywords -
        # concerns are outweighed by clarity of function argument names.

        # Weight is the count scaled to the min/max bounds
        # weight = ( (count * (max - min)) / max_count ) + min
        scale = int(max) - int(min)
        max_count = self.model.objects.aggregate(Max("count"))["count__max"] or 1
        qs = self.annotate(weight=(Floor(F("count") * scale) / max_count) + int(min))
        return qs

    def __str__(self):
        return utils.render_tags(self)


class BaseTagModelManager(models.Manager):
    def __str__(self):
        return str(self.get_queryset())


TagModelManager = BaseTagModelManager.from_queryset(TagModelQuerySet)

# ##############################################################################
# ###### Abstract base class for all TagModel models
# ##############################################################################

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Metaclass for tag models
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagModelBase(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        # Set up as normal
        new_cls = super(TagModelBase, cls).__new__(cls, name, bases, attrs)

        # TagMeta takes priority for the model
        new_tag_options = None
        if "TagMeta" in attrs:
            tag_meta = {}
            tag_meta = dict(
                (key, val)
                for key, val in attrs["TagMeta"].__dict__.items()
                if key in constants.OPTION_DEFAULTS
            )
            if "tree" in tag_meta:
                raise ValueError("Cannot set tree option in TagMeta")

            new_tag_options = TagOptions(**tag_meta)

        # Failing that, look for a direct tag_options setting
        # It will probably have been passed by BaseTagField.contribute_to_class
        elif "tag_options" in attrs:
            new_tag_options = attrs["tag_options"]

        # Otherwise start a new one
        else:
            new_tag_options = TagOptions()

        # See if there's anything to inherit
        # This also means that tag_options will be available on abstract models
        if hasattr(new_cls, "tag_options"):
            # Inherit by setting missing values in place
            new_tag_options.set_missing(new_cls.tag_options)

        # Assign
        new_cls.tag_options = new_tag_options

        # Check for self-referential tag fields on this model
        fields = new_cls._meta.fields + new_cls._meta.many_to_many

        for field in fields:
            # Can't test for subclass of field here - would be circular import
            if hasattr(field, "tag_model") and field.tag_model == new_cls:
                # This method is being called after the tag field's
                # contribute_to_class and _process_deferred_options. This means
                # that the field is using tag_options from the inherited model.
                # Change it to use this one
                field.tag_options = new_tag_options

        return new_cls


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Empty abstract model
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class BaseTagModel(models.Model, metaclass=TagModelBase):
    """
    Empty abstract base class for tag models

    This is used when dynamically building models, eg in migrations
    """

    objects = TagModelManager()

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)

    def __eq__(self, obj):
        """
        If comparing to a string, is equal if string value matches
        Otherwise compares normally
        """
        if isinstance(obj, str):
            return self.name == obj
        return super(BaseTagModel, self).__eq__(obj)

    __hash__ = models.Model.__hash__

    def __ne__(self, obj):
        return not self == obj

    def get_absolute_url(self):
        if self.tag_options.get_absolute_url is None:
            raise AttributeError(
                "'%s' has no attribute 'get_absolute_url'" % self.__class__.__name__
            )
        return self.tag_options.get_absolute_url(self)

    @classmethod
    def get_related_fields(cls, include_standard=False):
        """
        Return a list of related tag fields in other models which refer to this
        tag model.

        If include_standard=False (default), only SingleTagFields and
        TagFields will be returned. If True, it will also include ForeignKeys
        and ManyToManyFields.
        """
        # Avoid circular import
        from .fields import SingleTagField, TagField

        meta = cls._meta

        related_fields = [
            f
            for f in meta.get_fields()
            if (f.many_to_many or f.one_to_many or f.one_to_one) and f.auto_created
        ]

        if include_standard:
            return related_fields

        return [
            f
            for f in related_fields
            if isinstance(
                f.field,
                (
                    SingleTagField,
                    TagField,
                ),
            )
        ]

    def get_related_objects(self, flat=False, distinct=False, include_standard=False):
        """
        Get any instances of other models which refer to this tag instance

        If flat=False, returns the following data structure:
            [
                [related_model, related_field, [instance, instance, ...],
                [related_model, related_field, [instance, instance, ...],
                ...
            ]

        If flat=False, the distinct argument is ignored. Models and fields
        will only be included if they refer to this specific tag - there will
        not be any empty lists of instances.

        If flat=True, returns a list of instances without any information about
        how they are related:
            [ instance, instance, ... ]

        If flat=True and distinct=True, only unique instances will be returned.

        If include_standard=False (default), only SingleTagFields and
        TagFields will be returned. If True, it will also include ForeignKeys
        and ManyToManyFields.
        """
        data = []
        for related in self.get_related_fields(include_standard=include_standard):
            related_model = related.related_model

            objs = related_model._base_manager.using(
                router.db_for_write(self.tag_model)
            ).filter(**{"%s" % related.field.name: self})
            if not objs:
                continue
            if flat:
                data.extend(objs)
            else:
                data.append([related_model, related.field, objs])
        if flat and distinct:
            data = list(set(data))
        return data

    def update_count(self):
        """
        Count how many SingleTagFields and TagFields refer to this tag, save,
        and try to delete.
        """
        self.count = len(self.get_related_objects(flat=True))
        self.save()
        self.try_delete()

    update_count.alters_data = True

    def increment(self):
        """
        Increase the count by one
        """
        self._change_count(1)

    increment.alters_data = True

    def decrement(self):
        """
        Decrease the count by one, then try to delete
        """
        self._change_count(-1)

    decrement.alters_data = True

    def _change_count(self, amount):
        """
        Change count by amount
        """
        self.__class__.objects.filter(pk=self.pk).update(
            count=models.F("count") + amount
        )

        # Reload count
        # Use DB for write because we just updated the value
        using = router.db_for_write(self.tag_model, instance=self)
        self.refresh_from_db(using=using)

        self.try_delete()

    def try_delete(self):
        """
        If count is 0, try to delete this tag
        """
        if self.count != 0:
            return

        # See if it's protected
        is_protected = self.protected or self.tag_options.protect_all
        if not is_protected:
            # Before we delete, check for any standard relationships
            # This will catch if the tag is in a tree with children
            true_count = len(self.get_related_objects(flat=True, include_standard=True))
            if true_count > 0:
                # ForeignKeys or ManyToManyFields refer to it
                # We can't delete (we'll break things)
                # Tag is protected, for now
                is_protected = True

        # Try to delete
        if not is_protected:
            # Tag is not in use and not protected. Delete.
            self.delete()

            # If a tree, parent node may now be empty - try to delete it
            if self.tag_options.tree and self.parent:
                self.parent.try_delete()

    try_delete.alters_data = True

    def _prep_merge_tags(self, tags):
        """
        Ensure tags argument for merge_tags is an iterable of tag objects,
        excluding self
        """
        # Ensure tags is a list of tag instances
        if isinstance(tags, str):
            tags = utils.parse_tags(
                tags, space_delimiter=self.tag_options.space_delimiter
            )
        if not isinstance(tags, models.query.QuerySet):
            tags = self.tag_model.objects.filter(name__in=tags)

        # Make sure self isn't in tags
        return tags.exclude(pk=self.pk)

    def merge_tags(self, tags):
        """
        Merge the specified tags into this tag
        """
        # Avoid circular import
        from .fields import SingleTagField, TagField

        related_fields = self.tag_model.get_related_fields()
        tags = self._prep_merge_tags(tags)

        for related in related_fields:
            # Get the instances of the related models which refer to the tag
            # instances being merged
            related_model = related.related_model

            objs = related_model._base_manager.using(
                router.db_for_write(self.tag_model, instance=self)
            ).filter(**{"%s__in" % related.field.name: tags})

            # Switch the tags
            if isinstance(related.field, SingleTagField):
                for obj in objs:
                    setattr(obj, related.field.name, self)
                    obj.save()

            elif isinstance(related.field, TagField):
                for obj in objs:
                    getattr(obj, related.field.name).remove(*tags)
                    getattr(obj, related.field.name).add(self)

    merge_tags.alters_data = True

    def _update_extra(self):
        """
        Called by .save() before super().save()

        Allows subclasses to update extra fields based on slug
        """
        pass

    def _save_direct(self, *args, **kwargs):
        """
        Save without modifying data

        Used during schemamigrations
        """
        # We inherited from BaseTagModel, tell that to save directly too
        return super(BaseTagModel, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Automatically generate a unique slug, if one does not exist
        """
        # Based on django-taggit: don't worry about race conditions when
        # setting names and slugs, just avoid potential slugify clashes.
        # We could improve this if race conditions are ever a problem in the
        # real world, but until Django provides a reliable way to determine
        # the cause of an IntegrityError, we can never make this perfect.

        # If already in the database and has a slug set, just save as normal
        # Set slug to None to rebuild it
        if self.pk and self.slug:
            self._update_extra()
            return super(BaseTagModel, self).save(*args, **kwargs)

        # Set the slug using the label if possible (for TagTreeModel), else
        # the tag name.
        label = getattr(self, "label", self.name)
        slug_max_length = self.__class__._meta.get_field("slug").max_length
        if settings.SLUG_ALLOW_UNICODE:
            slug_base = slugify(label, allow_unicode=True)
        else:
            slug_base = slugify(label, allow_unicode=False)

            # Django 3.2 strips trailing and leading underscores; this risks creating an
            # empty slug for unconvertable characters, eg logographic characters. Ensure
            # they are not empty.
            if slug_base == "":
                slug_base = "_"

        # ASCII-ification can make a longer string
        self.slug = slug_base[:slug_max_length]
        self._update_extra()

        # Make sure we're using the same db at all times
        cls = self.__class__
        kwargs["using"] = kwargs.get("using") or router.db_for_write(cls, instance=self)

        # Try saving the slug - it'll probably be fine
        try:
            # If transaction supports atomic, we need to wrap the save call -
            # otherwise if save throws an exception it'll cause any current
            # queries to roll back
            with transaction.atomic():
                return super(BaseTagModel, self).save(*args, **kwargs)
        except IntegrityError:
            pass

        # Integrity error - something is probably not unique.
        # Assume it was the slug - make it unique by appending a number.
        # See which numbers have been used
        slug_base = slug_base[: slug_max_length - settings.SLUG_TRUNCATE_UNIQUE]
        based_objects = cls.objects.filter(slug__regex="^%s_[0-9]+$" % slug_base)
        based_slugs = list(based_objects.values_list("slug", flat=True))
        if len(based_slugs) == 0:
            # No numbered version of the slug exists
            number = 1
        else:
            numbers = [int(slug.rsplit("_", 1)[1]) for slug in based_slugs]
            number = sorted(numbers)[-1] + 1

        self.slug = "%s_%d" % (slug_base, number)
        self._update_extra()
        return super(BaseTagModel, self).save(*args, **kwargs)

    save.alters_data = True

    # For consistency with SingleTagField, provide .tag_model attribute
    tag_model = property(lambda self: self.__class__)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Abstract model with fields
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagModel(BaseTagModel):
    """
    Abstract base class for tag models
    """

    name = models.CharField(unique=True, max_length=settings.NAME_MAX_LENGTH)
    slug = models.SlugField(unique=False, max_length=settings.SLUG_MAX_LENGTH)
    count = models.IntegerField(
        default=0, help_text="Internal counter of how many times this tag is in use"
    )
    protected = models.BooleanField(
        default=False, help_text="Will not be deleted when the count reaches 0"
    )

    class Meta:
        abstract = True
        ordering = ("name",)
        # Slug field must be unique, but manage it with unique_together
        # so that subclasses can override
        unique_together = (("slug",),)


# ##############################################################################
# ###### TagTreeModel manager and queryset
# ##############################################################################


class TagTreeModelQuerySet(TagModelQuerySet):
    def _clean(self):
        """
        Return a clean copy of this class
        """
        kwargs = {"model": self.model, "using": self._db}
        if hasattr(self, "_hints"):
            kwargs["hints"] = self._hints
        return self.__class__(**kwargs)

    def with_ancestors(self):
        """
        Add selected tags' ancestors to current queryset
        """
        # Build list of all paths of all ancestors (and self)
        paths = []
        for path in self.values_list("path", flat=True):
            parts = utils.split_tree_name(path)
            paths += [path] + [
                utils.join_tree_name(parts[:i])  # Join parts up to i (misses last)
                for i in range(1, len(parts))  # Skip first (empty)
            ]
        return self._clean().filter(path__in=set(paths))

    def with_descendants(self):
        """
        Add selected tags' descendants to current queryset
        """
        # Build query of all matching paths, and all their sub-paths
        query = models.Q()
        for path in self.values_list("path", flat=True):
            query = (
                query | models.Q(path=path) | models.Q(path__startswith="%s/" % path)
            )
        return self._clean().filter(query)

    def with_siblings(self):
        """
        Add selected tags' siblings to current queryset
        """
        # Get all unique parent pks, except None
        parent_ids = set(self.values_list("parent_id", flat=True))
        has_none = None in parent_ids
        if has_none:
            parent_ids.remove(None)

        # If None is there, we need to test with isnull
        query = models.Q(parent_id__in=list(parent_ids))
        if has_none:
            query = query | models.Q(parent_id__isnull=True)

        return self._clean().filter(query)


class TagTreeModelManager(TagModelManager):
    def get_queryset(self):
        return TagTreeModelQuerySet(self.model, using=self._db)

    get_query_set = get_queryset

    def rebuild(self):
        """
        Re-save each instance to update tag fields
        """
        for tag in self.all():
            # Replace slug in case name has changed
            # If it hasn't, it'll just end up re-creating the same one
            tag.slug = None
            tag.save()

    rebuild.alters_data = True

    def as_nested_list(self):
        """
        Return all tags as a nested list, as lists of ``(tag, children)`` tuples in the
        format::

            [(tag, [child_tuple, ...]), ...]

        For example::

            [
                (level_1_tag_!, [
                    (level_2_tag_1, [...]),
                    (level_2_tag_2, [...]),
                ]),
                (level_1_tag_!, [...]),
            ]

        Will be in alphabetical order

        Note: this will cause the queryset to be evaluated
        """
        qs = self.all().order_by("name")
        root = []
        stack = []
        for tag in qs:
            # Top level tag restarts the stack and gets added to the root list
            if tag.level == 1:
                stack = [(tag, [])]
                root.append(stack[0])
                continue

            # Current deepest child is on the end of the stack
            current_tag, current_children = stack[-1]

            # This tag is a sibling or ancestor's sibling, move up the stack
            if tag.level <= current_tag.level:
                # Move up to the parent of the tag
                up = current_tag.level - (tag.level - 1)
                # ``up`` should never be less than 0 due to db constraints
                del stack[-up:]

                current_tag, current_children = stack[-1]

            # Due to db constraints At this point we must be adding a direct child
            # Record and add to the stack
            new_node = (tag, [])
            current_children.append(new_node)
            stack.append(new_node)

        return root


# ##############################################################################
# ###### Abstract base class for all TagTreeModel models
# ##############################################################################

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Metaclass for tag tree models
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagTreeModelBase(TagModelBase):
    def __new__(cls, name, bases, attrs):
        # Set up as normal
        new_cls = super(TagTreeModelBase, cls).__new__(cls, name, bases, attrs)

        # Force tree tag_options to True
        new_cls.tag_options.tree = True

        return new_cls


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Empty abstract model
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class BaseTagTreeModel(BaseTagModel, metaclass=TagTreeModelBase):
    """
    Empty abstract base class for tag models with tree

    This is used when dynamically building models, eg in migrations
    """

    objects = TagTreeModelManager()

    class Meta:
        abstract = True

    # Other derivable attributes won't be used in lookups, so don't need to be
    # cached. If there are situations where they are needed for lookups, this
    # model can be subclassed (or better yet, use a reusable mixin) and the
    # properties replaced by caching fields.
    def _get_descendant_count(self):
        "The sum of the counts of all descendants"
        return self.get_descendants().aggregate(models.Sum("count"))["count__sum"] or 0

    descendant_count = property(
        _get_descendant_count, doc=_get_descendant_count.__doc__
    )

    def _get_family_count(self):
        "The count of self plus all its descendants"
        return self.descendant_count + self.count

    family_count = property(_get_family_count, doc=_get_family_count.__doc__)

    def __init__(self, *args, **kwargs):
        """
        Initialise the tag
        """
        super(BaseTagTreeModel, self).__init__(*args, **kwargs)
        # Keep track of the name
        self._name = self.name

    def _save_direct(self, *args, **kwargs):
        """
        Save without modifying data

        Used during schemamigrations
        """
        # We inherited from BaseTagModel, tell that to save directly too
        return super(BaseTagTreeModel, self)._save_direct(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Set the parent and path cache
        """
        # Make sure name is valid
        if self.name is None or not self.name.strip():
            raise IntegrityError(
                "NOT NULL constraint failed: {}.name".format(self._meta.db_table)
            )
        self.name = utils.clean_tree_name(self.name)

        # Find the parent, or create it if missing
        parts = utils.split_tree_name(self.name)
        old_parent = self.parent
        if len(parts) > 1:
            self.parent, created = self.__class__.objects.get_or_create(
                name=utils.join_tree_name(parts[:-1])
            )
        else:
            self.parent = None

        # Update other cache fields
        self.label = parts[-1]
        self.level = len(parts)

        # Save - super .save() method will set the path using _get_path()
        super(BaseTagTreeModel, self).save(*args, **kwargs)

        # If name has changed...
        if self._name != self.name:
            # Update child names
            for child in self.children.all():
                child.name = utils.join_tree_name(parts + [child.label])
                child.save()
            self._name = self.name

            # Notify parent that it may now be empty
            if old_parent:
                old_parent.update_count()

    save.alters_data = True

    def _update_extra(self):
        """
        Updates extra fields based on slug
        """
        # Update the path
        if self.parent:
            self.path = "/".join([self.parent.path, self.slug])
        else:
            self.path = self.slug

    _update_extra.alters_data = True

    def merge_tags(self, tags, children=False):
        """
        Merge the specified tags into this tag

        If children is True, child tags will also be merged into children of
        this tag (retaining structure)
        """
        tags = self._prep_merge_tags(tags)

        # Merge children first
        if children:
            cls = self.__class__
            for tag in tags:
                for child in tag.children.all():
                    # Find merge target on this tree
                    new_child_name = "/".join([self.name, child.label])
                    try:
                        my_child = cls.objects.get(name=new_child_name)
                    except cls.DoesNotExist:
                        my_child = None

                    if my_child:
                        # It exists - merge recursively
                        my_child.merge_tags([child], children=True)
                    else:
                        # It doesn't exist - rename recursively
                        child.name = new_child_name
                        child.save()

        # Merge self
        super(BaseTagTreeModel, self).merge_tags(tags)

    merge_tags.alters_data = True

    def get_ancestors(self):
        """
        Get a queryset of ancestors for this tree node
        """
        cls = self.__class__
        if not self.parent:
            return cls.objects.none()

        # Get all ancestor paths from this path
        parts = utils.split_tree_name(self.path)
        paths = [
            utils.join_tree_name(parts[:i])  # Join parts up to i (misses last)
            for i in range(1, len(parts))  # Skip first (empty)
        ]

        # Look up ancestors by path, already ordered by name for deepest last
        return cls.objects.filter(path__in=paths)

    def get_descendants(self):
        """
        Get a queryset of descendants of this tree node
        """
        # Look up by path, already ordered by name for deepest last
        cls = self.__class__
        return cls.objects.filter(path__startswith="%s/" % self.path)

    def get_siblings(self):
        """
        Get a queryset of siblings of this tree node, including this node.

        If you don't want this node in the results, exclude it afterwards, eg:

            node.get_siblings().exclude(pk=node.pk)
        """
        if self.parent:
            return self.parent.children.all()
        return self.__class__.objects.filter(level=1)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Abstract model with fields
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class TagTreeModel(BaseTagTreeModel, TagModel):
    """
    Abstract base class for tag models with tree
    """

    # These fields are all generated automatically on save
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
        db_index=True,
    )
    path = models.TextField()
    label = models.CharField(
        max_length=settings.LABEL_MAX_LENGTH,
        help_text="The name of the tag, without ancestors",
    )
    level = models.IntegerField(default=1, help_text="The level of the tag in the tree")

    class Meta:
        abstract = True
        ordering = ("name",)
        unique_together = (("slug", "parent"),)
