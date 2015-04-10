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
        
    def update_count(self, count):
        """
        Update the count, then either save or delete the tag as appropriate
        """
        self.count = count
        if count == 0 and not self.protected and not self.tag_options.protect_all:
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
    
    def merge_tags(self, tags):
        """
        Merge the specified tags into this tag
        """
        model = self.model
        meta = model._meta
        if hasattr(meta, 'get_fields'):
            # Django 1.8
            related_fields = meta.get_fields(include_hidden=True)
        else:
            related_fields = meta.get_all_related_objects()
            related_fields += meta.get_all_related_many_to_many_objects()
        
        # Ensure tags is a list of tag instances
        if not isinstance(tags, models.query.QuerySet):
            tags = model.objects.filter(name__in=tags)
            
        # Make sure self isn't in tags
        tags = tags.exclude(pk=self.pk)
        
        for related in related_fields:
            # Get the related instances for this field
            objs = related.model._base_manager.using(
                router.db_for_write(self.model)
            ).filter(
                **{"%s__in" % related.field.name: tags}
            )
            
            # Switch the tags
            # Referring via tagulous to avoid circular references
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
    
    # For consistency with SingleTagField, provide .model attribute
    model = property(lambda self: self.__class__)
    
    class Meta:
        abstract = True
