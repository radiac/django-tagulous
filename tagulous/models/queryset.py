"""
Tagulous queryset extensions
"""
import operator

from django.db import models
from django.db import transaction

from tagulous.models.fields import SingleTagField, TagField
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


def enhance_queryset(queryset):
    """
    Monkey-patch a QuerySet object for enhanced tag support
    """
    old_filter_or_exclude = queryset._filter_or_exclude
    old_create = queryset.create
    old_get_or_create = queryset.get_or_create
    
    def new_filter_or_exclude(self, negate, *args, **kwargs):
        safe_fields, singletag_fields, tag_fields = split_kwargs(self.model, kwargs)
        
        # Look up string values for SingleTagFields by name
        for field_name, val in singletag_fields.items():
            if isinstance(val, basestring):
                field_name += '__name'
            safe_fields[field_name] = val
        
        # Query as normal
        qs = old_filter_or_exclude(self, negate, *args, **safe_fields)
        
        # Look up TagFields by string name
        for field_name, val in tag_fields.items():
            # Parse the tag string
            tags = utils.parse_tags(val)
            
            # Filter this queryset to include (or exclude) any items with a
            # tag count that matches the number of specified tags
            qs = new_filter_or_exclude(
                qs.annotate(count=models.Count(field_name)),
                negate, count=len(tags)
            )
            
            # Now AND Q objects of the tags to filter/exclude any items which
            # are tagged with all of these tags
            for tag in tags:
                qs = new_filter_or_exclude(
                    qs, negate, **{field_name + '__name': tag}
                )
        
        return qs
    
    def new_create(self, **kwargs):
        # Create object as normal
        safe_fields, singletag_fields, tag_fields = split_kwargs(self.model, kwargs)
        
        # Could convert SingleTagFields to instances with
        # field.tag_model.objects.get_or_create, but model constructor will
        # assign it through the descriptor anyway, so this is unnecessary.
        # SingleTagFields are safe
        safe_fields.update(singletag_fields)
        
        if hasattr(transaction, 'atomic'):
            with transaction.atomic():
                return _do_create(self, safe_fields, tag_fields)
                
        else:
            with transaction.commit_on_success():
                return _do_create(self, safe_fields, tag_fields)

    def _do_create(self, safe_fields, tag_fields):
        # Create as normal
        obj = old_create(self, **safe_fields)
        
        # Add tag fields
        for field_name, val in tag_fields.items():
            setattr(obj, field_name, val)
            getattr(obj, field_name).save()
            
        return obj
    
    def new_get_or_create(self, **kwargs):
        # Get or create object as normal
        safe_fields, singletag_fields, tag_fields = split_kwargs(self.model, kwargs)
        
        # As in new_create, SingleTagFields are ok to create, and new_get
        # will be fine for lookup
        safe_fields.update(singletag_fields)
        
        # Use normal get_or_create if there are no tag fields
        if len(tag_fields) == 0:
            return old_get_or_create(self, **safe_fields)
        
        # Try to find it using get - that is able to handle tag_fields
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return new_create(self, **kwargs), True
    
    # Apply patch
    queryset._filter_or_exclude = new_filter_or_exclude
    queryset.create = new_create
    queryset.get_or_create = new_get_or_create

if settings.ENHANCE_QUERYSET:
    enhance_queryset(models.query.QuerySet)




def enhance_model(model):
    old_init = model.__init__
    
    def new_init(self, *args, **kwargs):
        safe_fields, singletag_fields, tag_fields = split_kwargs(self, kwargs)
        
        # Constructor has always been happy with ForeignKeys
        safe_fields.update(singletag_fields)
        
        # Call old init
        old_init(self, *args, **safe_fields)
        
        # Add on TagField values
        for field_name, val in tag_fields.items():
            setattr(self, field_name, val)

    model.__init__ = new_init
    
if settings.ENHANCE_MODEL:
    enhance_model(models.Model)


