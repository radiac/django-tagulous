from django.db import models, router

import tagulous


#
# Abstract base class for all TagModel models
#
class BaseTagModel(models.Model):
    """
    Base tag model, without fields
    Required for South
    """
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
    def get_related_fields(cls):
        """
        Return a list of fields in other models which refer to this tag model
        """
        meta = cls._meta
        if hasattr(meta, 'get_fields'):
            # Django 1.8
            related_fields = meta.get_fields(include_hidden=True)
        else:
            related_fields = meta.get_all_related_objects()
            related_fields += meta.get_all_related_many_to_many_objects()
        return related_fields
        
    def get_related(self, flat=False, distinct=False):
        """
        Get any instances of other models which refer to this tag instance
        
        If flat=False, returns the following data structure:
            [
                [related_model, related_field, [instance, instance, ...],
                [related_model, related_field, [instance, instance, ...],
                ...
            ]
        
        If flat=False, the distinct argument is ignored.
        
        If flat=True, returns a list of instances without any information about
        how they are related:
            [ instance, instance, ... ]
        
        If flat=True and distinct=True, only unique instances will be returned.
        """
        data = []
        for related in self.get_related_fields():
            objs = related.model._base_manager.using(
                router.db_for_write(self.tag_model)
            ).filter(
                **{"%s" % related.field.name: self}
            )
            if flat:
                data.extend(objs)
            else:
                data.append(related, objs)
        if flat and distinct:
            list(set(data))
        return data
        
    def update_count(self, count=0):
        """
        Update the count, then either save or delete the tag as appropriate
        """
        # If count is 0, double check that's true
        if count == 0:
            
            self.count = count
        if count == 0 and not self.protected and not self.tag_options.protect_all:
            # ++ Double check count is actually true
            self.delete()
        else:
            self.count = count
            self.save()
    
    def increment(self):
        """
        Increase the count by one
        """
        self.update_count(self.count + 1)
    
    def decrement(self):
        """
        Decrease the count by one
        """
        self.update_count(self.count - 1)
    
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
                router.db_for_write(self.tag_model)
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
        
    class Meta:
        abstract = True
        
        
class TagModel(BaseTagModel):
    """
    Abstract base class for tag models
    """
    name        = models.CharField(max_length=255, unique=True)
    count       = models.IntegerField(default=0,
        help_text="Internal counter to keep track of how many relationships there are"
    )
    protected   = models.BooleanField(default=False,
        help_text="Will not be deleted when the count reaches 0"
    )
    
    # For consistency with SingleTagField, provide .tag_model attribute
    tag_model = property(lambda self: self.__class__)
    
    class Meta:
        abstract = True
