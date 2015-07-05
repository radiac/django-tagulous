"""
Tagulous extensions for models which use tag fields (tagged models)

These are all applied automatically when the TAGULOUS_ENHANCE_MODELS setting
is enabled.
"""

from django.db import models
from django.db import transaction

from tagulous.models.fields import (
    SingleTagField, TagField,
    singletagfields_from_model, tagfields_from_model,
)
from tagulous import settings
from tagulous import utils


def split_kwargs(model, kwargs):
    """
    Split kwargs into fields which are safe to pass to create, and
    m2m tag fields, creating SingleTagFields as required.
    
    Returns a tuple of safe_fields, singletag_fields, tag_fields
    """
    safe_fields = {}
    singletag_fields = {}
    tag_fields = {}
    for field_name, val in kwargs.items():
        # Try to look up the field
        try:
            field = model._meta.get_field(field_name)
        except models.fields.FieldDoesNotExist:
            # Assume it's something clever for get_or_create.
            # If it's invalid, an error will be raised later anyway
            safe_fields[field_name] = val
            continue
        
        # Take special measures depending on field type
        if isinstance(field, SingleTagField):
            singletag_fields[field_name] = val
            
        elif isinstance(field, TagField):
            # Store for later
            tag_fields[field_name] = val
        
        else:
            safe_fields[field_name] = val
    
    return safe_fields, singletag_fields, tag_fields



###############################################################################
############################################################### TaggedQuerySet
###############################################################################

class TaggedQuerySet(models.query.QuerySet):
    """
    A QuerySet with support for Tagulous tag fields
    """
    def _filter_or_exclude(self, negate, *args, **kwargs):
        safe_fields, singletag_fields, tag_fields = split_kwargs(self.model, kwargs)
        
        # Look up string values for SingleTagFields by name
        for field_name, val in singletag_fields.items():
            if isinstance(val, basestring):
                field_name += '__name'
            safe_fields[field_name] = val
        
        # Query as normal
        qs = super(TaggedQuerySet, self)._filter_or_exclude(
            negate, *args, **safe_fields
        )
        
        # Look up TagFields by string name
        for field_name, val in tag_fields.items():
            # Parse the tag string
            tags = utils.parse_tags(val)
            
            # Filter this queryset to include (or exclude) any items with a
            # tag count that matches the number of specified tags
            qs = qs.annotate(
                count=models.Count(field_name)
            )._filter_or_exclude(
                negate, count=len(tags)
            )
            
            # Now AND Q objects of the tags to filter/exclude any items which
            # are tagged with all of these tags
            for tag in tags:
                qs = qs._filter_or_exclude(
                    negate, **{field_name + '__name': tag}
                )
        
        return qs
    
    def create(self, **kwargs):
        # Create object as normal
        safe_fields, singletag_fields, tag_fields = split_kwargs(self.model, kwargs)
        
        # Could convert SingleTagFields to instances with
        # field.tag_model.objects.get_or_create, but model constructor will
        # assign it through the descriptor anyway, so this is unnecessary.
        # SingleTagFields are safe
        safe_fields.update(singletag_fields)
        
        if hasattr(transaction, 'atomic'):
            transaction_atomic = transaction.atomic
        else:
            transaction_atomic = transaction.commit_on_success
        
        with transaction_atomic():
            # Create as normal
            obj = super(TaggedQuerySet, self).create(**safe_fields)
            
            # Add tag fields
            for field_name, val in tag_fields.items():
                setattr(obj, field_name, val)
                getattr(obj, field_name).save()
                
            return obj
    
    def get_or_create(self, **kwargs):
        # Get or create object as normal
        safe_fields, singletag_fields, tag_fields = split_kwargs(self.model, kwargs)
        
        # As in .create, SingleTagFields are ok to create
        # Existing .get will be fine for lookup
        safe_fields.update(singletag_fields)
        
        # Use normal get_or_create if there are no tag fields
        if len(tag_fields) == 0:
            return super(TaggedQuerySet, self).get_or_create(**safe_fields)
        
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
        'CastTagged' to indicate the type of the object has changed, eg a normal
        QuerySet will become CastTaggedQuerySet.
        """
        # Make a subclass of TaggedQuerySet and the original class
        orig_cls = queryset.__class__
        queryset.__class__ = type(
            'CastTagged%s' % orig_cls.__name__, (cls, orig_cls), {},
        )
        return queryset


###############################################################################
############################################################### TaggedManager
###############################################################################


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
        
    def get_query_set(self, *args, **kwargs):
        """
        Get the original queryset and then enhance it (Django 1.5 or earlier)
        """
        qs = super(TaggedManager, self).get_query_set(*args, **kwargs)
        return self._enhance_queryset(qs)
    
    @classmethod
    def cast_class(cls, manager):
        """
        Changes the class of the specified manager to a subclass of TaggedManager
        and the original class, so it has all the same properties it did when it
        was first initialised, but is now a TaggedManager subclass.
        
        The new class is given the same name as the old class, but with the prefix
        'CastTagged' to indicate the type of the object has changed, eg a normal
        Manager will become CastTaggedManager
        """
        # Make a subclass of TaggedQuerySet and the original class
        orig_cls = manager.__class__
        manager.__class__ = type(
            'CastTagged%s' % orig_cls.__name__, (cls, orig_cls), {},
        )
        return manager
    

###############################################################################
############################################################### TaggedModel
###############################################################################

class TaggedModel(models.Model):
    """
    An abstract model base class with support for Tagulous tag fields
    """
    def __init__(self, *args, **kwargs):
        safe_fields, singletag_fields, tag_fields = split_kwargs(self, kwargs)
        
        # Constructor has always been happy with ForeignKeys
        safe_fields.update(singletag_fields)
        
        # Call old init
        super(TaggedModel, self).__init__(*args, **safe_fields)
        
        # Add on TagField values
        for field_name, val in tag_fields.items():
            setattr(self, field_name, val)
    
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
        
        # If there are no tag fields, or it's already a TaggedModel, skip
        if not tag_fields or issubclass(model, TaggedModel):
            return
        
        # Make the model subclass TaggedModel
        model.__bases__ = (TaggedModel,) + model.__bases__
        
        # Make the managers subclass TaggedManager
        if (
            hasattr(model, 'objects')
            and not issubclass(model.objects.__class__, TaggedManager)
        ):
            TaggedManager.cast_class(model.objects)
        
        return model
    
    class Meta:
        abstract = True


###############################################################################
# Start automatic enhancement
###############################################################################

if settings.ENHANCE_MODELS:
    def class_prepared_listener(sender, **kwargs):
        """
        Listen to the class_prepared signal and subclass any model with tag
        fields
        """
        TaggedModel.cast_class(sender)
    models.signals.class_prepared.connect(class_prepared_listener, weak=False)
