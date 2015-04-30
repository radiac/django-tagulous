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
        return TagModelQuerySet(self.model)
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
    
    def increment(self):
        """
        Increase the count by one
        """
        self._change_count(1)
    
    def decrement(self):
        """
        Decrease the count by one, then try to delete
        """
        self._change_count(-1)
    
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
       
        # Try to delete
        if not is_protected:
            # Tag is not in use and not protected. Delete.
            self.delete()
    
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
    
    def save(self, *args, **kwargs):
        """
        Automatically generate a unique slug, if one does not exist
        """
        # Based on django-taggit: don't worry about race conditions when
        # setting names and slugs, just avoid potential slugify clashes.
        # We could improve this if race conditions are ever a problem in the
        # real world, but until Django provides a reliable way to determine
        # the cause of an IntegrityError, we can never make this perfect.
        
        # If already in the database, or has a slug, just save as normal
        if self.pk or self.slug:
            return super(BaseTagModel, self).save(*args, **kwargs)
        
        # Set the slug
        self.slug = slugify(self.name)
        
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
        return super(BaseTagModel, self).save(*args, **kwargs)
        
    class Meta:
        abstract = True
        
        
###############################################################################
####### Abstract base class for tag models
###############################################################################

class TagModel(BaseTagModel):
    """
    Abstract base class for tag models
    """
    name        = models.CharField(max_length=255, unique=True)
    slug        = models.SlugField(unique=True)
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

