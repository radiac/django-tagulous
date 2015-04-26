from django import forms
from django.db.models.query import QuerySet
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import EMPTY_VALUES
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.encoding import force_unicode

# ++ Can remove this try/except when min req is Django 1.5
try:
    import json
except ImportError:
   from django.utils import simplejson as json

from tagulous import settings
from tagulous.models import options
from tagulous.utils import parse_tags, render_tags


class TagWidgetBase(forms.TextInput):
    """
    Base class for tags
    """
    # Attributes that subclasses must set
    autocomplete_settings = None
    
    # Attributes that the calling Field must set
    tag_options = None
    autocomplete_tags = None
    
    # Based on django-taggit
    def render(self, name, value, attrs={}):
        # Try to provide a URL for the autocomplete to load tags on demand
        autocomplete_view = self.tag_options.autocomplete_view
        if autocomplete_view:
            try:
                attrs['data-tag-url'] = reverse(self.autocomplete_view)
            except Exception, e:
                raise ValueError('Invalid autocomplete view: %s' % e)
        
        # Otherwise embed them, if provided
        elif self.autocomplete_tags:
            autocomplete_tags = self.autocomplete_tags
            # If it's a queryset, make sure it hasn't been consumed, otherwise
            # changes won't show in the list
            if isinstance(autocomplete_tags, QuerySet):
                autocomplete_tags = autocomplete_tags.all()
                
            attrs['data-tag-list'] = escape(force_unicode(
                json.dumps(
                    [str(tag) for tag in autocomplete_tags],
                    cls=DjangoJSONEncoder,
                )
            ))
        
        # Merge default autocomplete settings into tag options
        tag_options = self.tag_options.field_items(with_defaults=False)
        if (
            'autocomplete_settings' not in tag_options
            and self.default_autocomplete_settings is not None
        ):
            tag_options['autocomplete_settings'] = self.default_autocomplete_settings
        
        # Inject extra settings
        tag_options.update({
            'required': self.is_required,
        })
        
        # Store tag options
        attrs['data-tag-options'] = escape(force_unicode(
            json.dumps(tag_options, cls=DjangoJSONEncoder)
        ))
        
        # Mark it for the javascript to find
        attrs['data-tagulous'] = 'true'
        
        # Turn off browser's autocomplete
        attrs['autocomplete'] = 'off'
        
        # Render value
        return super(TagWidgetBase, self).render(name, value, attrs)


class TagWidget(TagWidgetBase):
    """
    Tag widget for public-facing forms
    """
    default_autocomplete_settings = settings.AUTOCOMPLETE_SETTINGS
    class Media:
        css = settings.AUTOCOMPLETE_CSS
        js = settings.AUTOCOMPLETE_JS


class AdminTagWidget(TagWidgetBase):
    """
    Tag widget for admin forms
    """
    default_autocomplete_settings = settings.ADMIN_AUTOCOMPLETE_SETTINGS
    class Media:
        css = settings.ADMIN_AUTOCOMPLETE_CSS
        js = settings.ADMIN_AUTOCOMPLETE_JS

    # Admin will be expecting this to have a choices attribute
    # Set this so the admin will behave as expected
    choices = None


class TagField(forms.CharField):
    widget = TagWidget
    
    def __init__(self, tag_options=None, autocomplete_tags=None, **kwargs):
        """
        Takes all CharField options, plus:
            tag_options         A TagOptions instance
                                If not provided, uses Tagulous defaults
            autocomplete_tags   Iterable of tags to be used for autocomplete,
                                ie a queryset from a TagModel, or a list of
                                strings. Will be ignored if tag_options
                                contains autocomplete_view
        """
        # Initialise as normal
        super(TagField, self).__init__(**kwargs)
        
        # Add tag options and autocomplete tags
        # Will use getters and setters to mirror onto widget
        self.tag_options = tag_options or options.TagOptions()
        self.autocomplete_tags = autocomplete_tags
        
    def prepare_value(self, value):
        """
        Prepare the value
        """
        # Catch no value (empty form for add)
        if not value:
            tag_string = value
            
        # If called by the form or as a SingleTagField, will get a string
        elif isinstance(value, basestring):
            tag_string = value
        
        # Otherwise will be given by the model's TagField.value_from_object().
        # The value comes from django.forms.model.model_to_dict, which thinks
        # it produced a list of pks but TagField.value_from_object tricked it
        else:
            # Catch changes in model_to_dict which broke the trick
            if len(value) != 1:
                raise ValueError(_("TagField could not prepare unexpected value"))
            tag_string = value[0]
            
        return super(TagField, self).prepare_value(tag_string)
    
    # Use setters and getters to ensure any changes to the field are mirrored
    # in the widget, in the same way ModelChoiceField mirrors its queryset
    def _get_tag_options(self):
        return self._tag_options
    def _set_tag_options(self, tag_options):
        self._tag_options = tag_options
        self.widget.tag_options = tag_options
    tag_options = property(_get_tag_options, _set_tag_options)
    
    def _get_autocomplete_tags(self):
        return self._autocomplete_tags
    def _set_autocomplete_tags(self, autocomplete_tags):
        self._autocomplete_tags = autocomplete_tags
        self.widget.autocomplete_tags = autocomplete_tags
    autocomplete_tags = property(_get_autocomplete_tags, _set_autocomplete_tags)
    
    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {}
        
    def clean(self, value):
        value = super(TagField, self).clean(value)
        
        if self.tag_options.force_lowercase:
            value = value.lower()
        
        try:
            return parse_tags(value, self.tag_options.max_count)
        except ValueError, e:
            raise forms.ValidationError(_('%s' % e))
        

class SingleTagField(TagField):
    """
    A single tag field assumes the contents is in " quotes
    """
    def prepare_value(self, value):
        """
        Prepare the value by stripping quotes
        """
        if value:
            if value.startswith('"') and value.endswith('"'):
                tag_string = value[1:-1]
            else:
                tag_string = value
            
            if '"' in tag_string:
                tag_string = tag_string.replace('"', '')
        else:
            tag_string = value
        
        return super(TagField, self).prepare_value(tag_string)

    def validate(self, value):
        """
        Validate by ensuring no quotes other than those at the start and end
        """
        # Validation only cares about the string itself
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        
        # Validation by parent class will expect empty value to be None
        super(SingleTagField, self).validate(value)
        if '"' in value:
            raise ValidationError('This field cannot contain the " character')
      
    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        attrs = super(SingleTagField, self).widget_attrs(widget)
        attrs.update({
            'data-tag-type': 'single',
        })
        return attrs
        
    def clean(self, value):
        """
        Clean by parsing tag with quotes
        """
        # From django 1.6 onwards, this is accessible on self.empty_values,
        # but should be fine to use directly for a descendant of CharField.
        if value not in EMPTY_VALUES:
            value = '"%s"' % value
        tags = super(SingleTagField, self).clean(value)
        if tags:
            return tags[0]
        else:
            return None
