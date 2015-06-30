"""
Tagulous tag models
"""

from django.db import models, router, IntegrityError
try:
    from django.utils.text import slugify
except ImportError:
    # Django 1.4 or earlier
    from django.template.defaultfilters import slugify

import tagulous
from tagulous import utils


###############################################################################
####### TagModel manager and queryset
###############################################################################

class TagModelQuerySet(models.query.QuerySet):
    def filter_or_initial(self, *args, **kwargs):
        """
        Reduce the queryset to match the specified filter, but also include
        any initial tags left in the queryset.
        """
        return super(TagModelQuerySet, self).filter(
            models.Q(*args, **kwargs) |
            models.Q(name__in=self.model.tag_options.initial)
        )


class TagModelManager(models.Manager):
    def get_queryset(self):
        return TagModelQuerySet(self.model, using=self._db)
    get_query_set = get_queryset
    
    def filter_or_initial(self, *args, **kwargs):
        return self.get_queryset().filter_or_initial(*args, **kwargs)


###############################################################################
####### Abstract base class for all TagModel models
###############################################################################

class BaseTagModel(models.Model):
    """
    Base tag model, without fields
    Required for South
    """
    objects = TagModelManager()
    
    class Meta:
        abstract = True
        
    def __unicode__(self):
        return u'%s' % self.name
        
    def __eq__(self, obj):
        """
        If comparing to a string, is equal if string value matches
        Otherwise compares normally
        """
        if isinstance(obj, basestring):
            return self.name == obj
        return super(BaseTagModel, self).__eq__(obj)

    def __ne__(self, obj):
        return not self == obj
    
    def get_absolute_url(self):
        if self.tag_options.get_absolute_url is None:
            raise AttributeError(
                "type object '%s' has no attribute 'get_absolute_url'" % self.__class__.__name__
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
        
        In Django 1.7 it will be a list RelatedObjects.
        """
        meta = cls._meta
        if hasattr(meta, 'get_fields'):
            ##38# ++ Django 1.8
            # ++ Looks like this won't work - not list of RelatedObjects
            related_fields = meta.get_fields(include_hidden=True)
        else:
            related_fields = meta.get_all_related_objects()
            related_fields += meta.get_all_related_many_to_many_objects()
        if include_standard:
            return related_fields
        return [
            f for f in related_fields
            if isinstance(f.field, (
                tagulous.models.fields.SingleTagField,
                tagulous.models.fields.TagField,
            ))
        ]
        
    def get_related_objects(
        self, flat=False, distinct=False, include_standard=False,
    ):
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
            if not include_standard and not isinstance(related.field, (
                tagulous.models.fields.SingleTagField,
                tagulous.models.fields.TagField,
            )):
                continue
            
            objs = related.model._base_manager.using(
                router.db_for_write(self.tag_model)
            ).filter(
                **{"%s" % related.field.name: self}
            )
            if not objs:
                continue
            if flat:
                data.extend(objs)
            else:
                data.append([related.model, related.field, objs])
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
            count=models.F('count') + amount
        )
        
        # Reload count
        if hasattr(self, 'refresh_from_db'):
            ##38# Django 1.8
            self.refresh_from_db()
        else:
            self.count = self.__class__.objects.get(pk=self.pk).count
        
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
            true_count = len(
                self.get_related_objects(flat=True, include_standard=True)
            )
            if true_count > 0:
                # ForeignKeys or ManyToManyFields refer to it
                # We can't delete (we'll break things)
                # Tag is protected, for now
                is_protected = True
        
        # See if it has children
        if (
            not is_protected
            and self.tag_options.tree
            and self.children.count() > 0
        ):
            # Can't delete if it has children
            is_protected = True
        
        # Try to delete
        if not is_protected:
            # Tag is not in use and not protected. Delete.
            self.delete()
            
            # If a tree, parent node may now be empty - try to delete it
            if self.tag_options.tree and self.parent:
                self.parent.try_delete()
    try_delete.alters_data = True
    
    def merge_tags(self, tags):
        """
        Merge the specified tags into this tag
        """
        related_fields = self.tag_model.get_related_fields()
        
        # Ensure tags is a list of tag instances
        if not isinstance(tags, models.query.QuerySet):
            tags = self.tag_model.objects.filter(name__in=tags)
            
        # Make sure self isn't in tags
        tags = tags.exclude(pk=self.pk)
        
        for related in related_fields:
            # Get the instances of the related models which refer to the tag
            # instances being merged
            objs = related.model._base_manager.using(
                router.db_for_write(self.tag_model, instance=self)
            ).filter(
                **{"%s__in" % related.field.name: tags}
            )
            
            # Switch the tags
            # Referring via tagulous to avoid circular import
            if isinstance(related.field, tagulous.models.SingleTagField):
                for obj in objs:
                    setattr(obj, related.field.name, self)
                    obj.save()
                    
            elif isinstance(related.field, tagulous.models.TagField):
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
        # the tag name
        label = getattr(self, 'label', self.name)
        self.slug = slugify(unicode(label))
        self._update_extra()
        
        # Make sure we're using the same db at all times
        cls = self.__class__
        kwargs['using'] = kwargs.get('using') or router.db_for_write(
            cls, instance=self
        )
        
        # Try saving the slug - it'll probably be fine
        try:
            return super(BaseTagModel, self).save(*args, **kwargs)
        except IntegrityError:
            pass
        
        # Integrity error - something is probably not unique.
        # Assume it was the slug - make it unique by appending a number.
        # See which numbers have been used
        slug_base = self.slug
        try:
            last = cls.objects.filter(
                slug__regex="^%s_\d+$" % slug_base
            ).latest('slug')
        except cls.DoesNotExist:
            # No numbered version of the slug exists
            number = 1
        else:
            slug_base, number = last.slug.rsplit('_', 1)
            number = int(number) + 1
        
        self.slug = '%s_%d' % (self.slug, number)
        self._update_extra()
        return super(BaseTagModel, self).save(*args, **kwargs)
    save.alters_data = True


###############################################################################
####### Abstract base class for tag models
###############################################################################

class TagModel(BaseTagModel):
    """
    Abstract base class for tag models
    """
    name        = models.CharField(max_length=255, unique=True)
    slug        = models.SlugField(
        unique=False,
        # Slug field must be unique, but manage it with Meta.unique_together
        # so that subclasses can override
    )
    count       = models.IntegerField(
        default=0,
        help_text="Internal counter of how many times this tag is in use"
    )
    protected   = models.BooleanField(
        default=False,
        help_text="Will not be deleted when the count reaches 0"
    )
    
    # For consistency with SingleTagField, provide .tag_model attribute
    tag_model = property(lambda self: self.__class__)
    
    class Meta:
        abstract = True
        ordering = ('name',)
        unique_together = (
            ('slug',),
        )


###############################################################################
####### TagTreeModel manager and queryset
###############################################################################


class TagTreeModelManager(TagModelManager):
    def rebuild(self):
        # Now re-save each instance to update tag fields
        for tag in self.all():
            tag.save()
    rebuild.alters_data = True



###############################################################################
####### Abstract base class for all TagModel models
###############################################################################

class TagTreeModel(TagModel):
    """
    Abstract base class for tag models with tree
    """
    # These fields are all generated automatically on save
    parent      = models.ForeignKey(
        'self', null=True, blank=True, related_name='children', db_index=True,
    )
    path        = models.TextField(unique=True)
    
    objects = TagTreeModelManager()
    
    class Meta:
        abstract = True
        ordering = ('name',)
        unique_together = (
            ('slug', 'parent'),
        )
    
    
    # Other derivable attributes won't be used in lookups, so don't need to be
    # cached. If they are needed for lookups, this model can be subclassed and
    # the properties replaced by caching fields.
    def _get_label(self):
        "The name of the tag, without ancestors"
        return utils.split_tree_name(self.name)[-1]
    label = property(_get_label, doc=_get_label.__doc__)
    
    def _get_depth(self):
        "The depth of the tag in the tree"
        return len(utils.split_tree_name(self.path))
    depth = property(_get_depth, doc=_get_depth.__doc__)
    
    def __init__(self, *args, **kwargs):
        """
        Initialise the tag
        """
        super(TagTreeModel, self).__init__(*args, **kwargs)
        # Keep track of the name
        self._name = self.name
    
    def save(self, *args, **kwargs):
        """
        Set the parent and path cache
        """
        # Make sure name is valid
        self.name = utils.clean_tree_name(self.name)
        
        # Find the parent, or create it if missing
        parts = utils.split_tree_name(self.name)
        if len(parts) > 1:
            self.parent, created = self.__class__.objects.get_or_create(
                name=utils.join_tree_name(parts[:-1])
            )
        else:
            self.parent = None
        
        # Save - super .save() method will set the path using _get_path()
        super(TagTreeModel, self).save(*args, **kwargs)
        
        # If name has changed, update child names
        if self._name != self.name:
            for child in self.children.all():
                child.name = utils.join_tree_name(parts + [child.label])
                child.save()
            self._name = self.name
    save.alters_data = True
    
    def _update_extra(self):
        """
        Updates extra fields based on slug
        """
        # Update the path
        if self.parent:
            self.path = '/'.join([self.parent.path, self.slug])
        else:
            self.path = self.slug
    _update_extra.alters_data = True
    
    
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
            utils.join_tree_name(parts[:i]) # Join parts up to i (misses last)
            for i in range(1, len(parts))   # Skip first (empty)
        ]
        
        # Look up ancestors by path, already ordered by name for deepest last
        return cls.objects.filter(path__in=paths)
    
    def get_descendants(self):
        """
        Get a queryset of descendants of this tree node
        """
        # Look up by path, already ordered by name for deepest last
        cls = self.__class__
        return cls.objects.filter(path__startswith='%s/' % self.path)
