"""
Tagulous model field managers

These are accessed via the descriptors, and do the work of storing and loading
the tags.
"""

from django.core import exceptions

from tagulous.utils import parse_tags, render_tags


class BaseTagManager(object):
    """
    Base class for SingleTagManager and RelatedManagerTagMixin
    """
    def __eq__(self, other):
        """
        Treat the other value as a string and compare to tags
        """
        other_str = u"%s" % other
        
        # Enforce case non-sensitivity or lowercase
        lower = False
        if self.tag_options.force_lowercase or not self.tag_options.case_sensitive:
            lower = True
            other_str = other_str.lower()
        
        # Parse other_str into list of tags
        other_tags = parse_tags(other_str)
        
        # Get list of set tags
        self_tags = self.get_tag_list()
        
        # Compare tag count
        if len(other_tags) != len(self_tags):
            return False
        
        # ++ Could optimise comparison for lots of tags by using an object
        
        # Compare tags
        for tag in self_tags:
            # If lowercase or not case sensitive, lower for comparison
            if lower:
                tag = tag.lower()
            
            # Check tag in other tags
            if tag not in other_tags:
                return False
        
        # Same number of tags, and all self tags present in other tags
        # It's a match
        return True
        
    def __ne__(self, other):
        return not self.__eq__(other)
        

# ++ Test single tag manager
class SingleTagManager(BaseTagManager):
    """
    Manage single tags - behaves like a descriptor, but holds additional
    information about the tag field between saves
    """
    def __init__(self, descriptor, instance):
        # The SingleTagDescriptor and instance this manages
        self.descriptor = descriptor
        self.instance = instance
        
        # Other vars we need
        self.tag_model = self.descriptor.tag_model
        self.field = self.descriptor.field
        self.tag_options = self.descriptor.tag_options
        
        # Keep track of unsaved changes
        self.changed = False
        
        # The descriptor stores an unsaved tag string
        # Start of with the actual value, if it exists
        self.tag_cache = self.get_actual()
        self.tag_name = self.tag_cache.name if self.tag_cache else None
        
        # Pre/post save will need to keep track of an old tag
        self.removed_tag = None
        
    def flush_actual(self):
        # Flush the cache of actual
        cache_name = self.field.get_cache_name()
        if hasattr(self.instance, cache_name):
            delattr(self.instance, cache_name)
        
    def get_actual(self):
        # A ForeignKey would be on the .attname (field_id), but only
        # if it has been set, otherwise the attribute will not exist
        
        # ++ Init should not be calling this in django's normal world
        # ++ So we need to either stop doing that, or add a flag to get_actual
        # which only tests if the instance exists, or value!=None
        # ++ Think this is fixed now?
        if hasattr(self.instance, self.field.attname):
        #if getattr(self.instance, self.field.attname, None):
            return self.descriptor.descriptor.__get__(self.instance)
        return None
    
    def set_actual(self, value):
        return self.descriptor.descriptor.__set__(self.instance, value)
        
    
    def get_tag_string(self):
        """
        Get the tag edit string for this instance as a string
        """
        if not self.instance:
            raise AttributeError("Function get_tag_string is only accessible via an instance")
        
        return render_tags( self.get() )
    
    def get_tag_list(self):
        """
        Get the tag names for this instance as a list of tag names
        """
        if not self.instance:
            raise AttributeError("Function get_tag_list is only accessible via an instance")
        
        return [tag.name for tag in self.get() ]
        
    def get(self):
        """
        Get the current tag - either a Tag object or None
        If the field has been changed since the instance was last saved, the
        Tag object may be a dynamically generated Tag which does not exist in
        the database yet. The count will not be updated until the instance is
        next saved.
        """
        # If changed, find the tag
        if self.changed:
            if not self.tag_name:
                return None
            
            # Try to look up the tag
            try:
                if self.tag_options.case_sensitive:
                    tag = self.tag_model.objects.get(name=self.tag_name)
                else:
                    tag = self.tag_model.objects.get(name__iexact=self.tag_name)
            except self.tag_model.DoesNotExist:
                # Does not exist yet, create a temporary one (but don't save)
                if not self.tag_cache:
                    self.tag_cache = self.tag_model(name=self.tag_name, protected=False)
                tag = self.tag_cache
            return tag
        else:
            # Return the response that it should have had (a Tag or None)
            return self.get_actual()
        
    def set(self, value):
        """
        Set the current tag
        """
        # Parse a tag string
        if not value:
            tag_name = ''
            
        elif isinstance(value, basestring):
            # Force tag to lowercase
            if self.tag_options.force_lowercase:
                value = value.lower()
                
            # Remove quotes from value to ensure it's a valid tag string
            tag_name = value.replace('"', '') or None
            
        # Look up the tag name
        else:
            tag_name = value.name
        
        # If no change, do nothing
        if self.tag_name == tag_name:
            return
        
        # Store the tag name and mark changed
        self.changed = True
        self.tag_name = tag_name
        self.tag_cache = None
        
    def pre_save_handler(self):
        """
        When the model is about to save, update the tag value
        """
        # Get the new tag
        new_tag = self.get()
        
        # Logic check to replace standard null/blank model field validation
        if not new_tag and self.field.required:
            raise exceptions.ValidationError(self.field.error_messages['null'])
        
        # Only need to go further if there has been a change
        if not self.changed:
            return
        
        # Store the old tag so we know to decrement it in post_save
        self.flush_actual()
        self.removed_tag = self.get_actual()
        
        # Create or increment the tag object
        if new_tag:
            # Ensure it is in the database
            if not new_tag.pk:
                new_tag.save()
                
            # Increment the new tag
            new_tag.increment()
        
        # Set it
        self.set_actual(new_tag)
        
        # Clear up
        self.changed = False
        
    def post_save_handler(self):
        """
        When the model has saved, decrement the old tag
        """
        if self.removed_tag:
            self.removed_tag.decrement()
            
    def post_delete_handler(self):
        """
        When the model has been deleted, decrement the actual tag
        """
        # Decrement the actual tag
        self.flush_actual()
        old_tag = self.get_actual()
        if old_tag:
            old_tag.decrement()
            self.set_actual(None)
            
            # If there is no new value, mark the old one as a new one,
            #  so the database will be updated if the instance is saved again
            if not self.changed:
                self.tag_name = old_tag.name
            self.tag_cache = None
            self.changed = True
        

        
class RelatedManagerTagMixin(BaseTagManager):
    """
    Mixin for RelatedManager to add tag functions
    """
    #
    # New add, remove and clear, to update tag counts
    # Will be switched into place by TagDescriptor
    #
    def _add(self, *objs):
        self._old_add(*objs)
        for tag in objs:
            tag.increment()
    _add.alters_data = True
    
    def _remove(self, *objs):
        self._old_remove(*objs)
        for tag in objs:
            tag.decrement()
    _remove.alters_data = True

    def _clear(self):
        tags = list(self.all())
        self._old_clear()
        for tag in tags:
            tag.decrement()
    _clear.alters_data = True
    
        
    #
    # Functions for getting and setting tags
    #
    
    def get_tag_string(self):
        """
        Get the tag edit string for this instance as a string
        """
        if not self.instance:
            raise AttributeError("Function get_tag_string is only accessible via an instance")
        
        return render_tags( self.all() )
    
    def get_tag_list(self):
        """
        Get the tag names for this instance as a list of tag names
        """
        # ++ Better as get_tag_strings?
        if not self.instance:
            raise AttributeError("Function get_tag_list is only accessible via an instance")
        
        return [tag.name for tag in self.all() ]
        
    def set_tag_string(self, tag_string):
        """
        Sets the tags for this instance, given a tag edit string
        """
        if not self.instance:
            raise AttributeError("Function set_tag_string is only accessible via an instance")
        
        # Get all tag names
        tag_names = parse_tags(tag_string)
        
        # Pass on to set_tag_list
        return self.set_tag_list(tag_names)
    set_tag_string.alters_data = True
        
    def set_tag_list(self, tag_names):
        """
        Sets the tags for this instance, given a list of tag names
        """
        if not self.instance:
            raise AttributeError("Function set_tag_list is only accessible via an instance")
        
        if self.tag_options.max_count and len(tag_names) > self.tag_options.max_count:
            raise ValueError("Cannot set more than %d tags on this field" % self.tag_options.max_count)
        
        # Force tag_names to unicode strings, just in case
        tag_names = [u'%s' % tag_name for tag_name in tag_names]
        
        # Find tag model
        tag_model = self.tag_model
        
        # Get list of current tags
        old_tags = self.all()
        
        # See which tags are staying and which are being removed
        current_names = []
        for tag in old_tags:
            # If a tag is not in the new list, remove it
            if tag.name not in tag_names:
                self.remove(tag)
                
            # Otherwise note it
            else:
                current_names.append(tag.name)
        
        # Find or create these tags
        for tag_name in tag_names:
            # Force tags to lowercase
            if self.tag_options.force_lowercase:
                tag_name = tag_name.lower()
            
            # If this is already in there, don't do anything
            if tag_name in current_names:
                continue
            
            # Find or create the tag
            # Do it manually, there's a problem with get_or_create, iexact and unique
            try:
                if self.tag_options.case_sensitive:
                    tag = tag_model.objects.get(name=tag_name)
                else:
                    tag = tag_model.objects.get(name__iexact=tag_name)
            except tag_model.DoesNotExist:
                tag = tag_model.objects.create(name=tag_name, protected=False)
            
            # Add the tag to this
            self.add(tag)
    
    set_tag_list.alters_data = True
    
    def __unicode__(self):
        """
        If called on an instance, return the tag string
        """
        if hasattr(self, 'instance'):
            return self.get_tag_string()
        else:
            return super(RelatedManagerTagMixin, self).__str__()
            
    def __str__(self):
        return unicode(self).encode('utf-8')

