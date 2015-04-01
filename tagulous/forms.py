from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.encoding import force_unicode

# ++ Can remove this try/except when min req is Django 1.5
try:
    import json
except ImportError:
   from django.utils import simplejson as json

from tagulous import settings
#from tagulous import models
from tagulous.utils import parse_tags, edit_string_for_tags


class TagWidgetBase(forms.TextInput):
    """
    Base class for tags
    """
    # Attributes that subclasses must set
    autocomplete_settings = None
    
    # Attributes that the calling Field must set
    tag_options = None
    autocomplete = None
    autocomplete_url = None
    autocomplete_view = None
    
    # Based on django-taggit
    def render(self, name, value, attrs={}):
        # Build data attrs
        if self.autocomplete:
            attrs['data-tag-autocomplete'] = escape(force_unicode(
                json.dumps(
                    [tag.name for tag in self.autocomplete],
                    cls=DjangoJSONEncoder,
                )
            ))
        elif self.autocomplete_view:
            try:
                attrs['data-tag-autocomplete-url'] = reverse(self.autocomplete_view)
            except Exception, e:
                # If we can't resolve it, fail silently
                pass
        
        # Merge default autocomplete settings into tag options
        tag_options = self.tag_options.field_items()
        autocomplete_settings = {}
        autocomplete_settings.update(
            self.default_autocomplete_settings,
            tag_options.get('autocomplete_settings', {}),
        )
        tag_options['autocomplete_settings'] = autocomplete_settings
        
        # Store tag options
        attrs['data-tag-options'] = escape(force_unicode(
            json.dumps(tag_options, cls=DjangoJSONEncoder)
        ))
        
        # Mark it for the javascript to find
        attrs['data-tag-tagulous'] = 'true'
        
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
    
    def __init__(self, tag_options, autocomplete=None,
        autocomplete_url=None, autocomplete_view=None,
        **kwargs
    ):
        """
        Takes all CharField options, plus:
            tag_options     A TagOptions instance
                            If not provided, uses Tagulous defaults
            autocomplete    Queryset of Tags that can be used for autocomplete
                            Note: autocomplete_embed_limit and autocomplete_url
                            will be ignored; the full queryset will be embedded
        """
        self.tag_options = tag_options# or models.TagOptions()
        self.autocomplete = autocomplete
        self.autocomplete_url = autocomplete_url
        self.autocomplete_view = autocomplete_view
        super(TagField, self).__init__(**kwargs)
        
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

    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        # Add tag options and autocomplete to the widget
        widget.tag_options = self.tag_options
        widget.autocomplete = self.autocomplete
        widget.autocomplete_url = self.autocomplete_url
        widget.autocomplete_view = self.autocomplete_view
        
        # But nothing to add yet
        return {}
        
    def clean(self, value):
        value = super(TagField, self).clean(value)
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
        if not (value.startswith('"') and value.endswith('"')):
            raise ValidationError('This field value must start and end with " character')
        
        # Rest of validation only cares about the string itself
        true_value = value[1:-1]
        
        # Validation by parent class will expect empty value to be None
        super(SingleTagField, self).validate(true_value)
        if '"' in true_value:
            raise ValidationError('This field cannot contain the " character')
      
    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        attrs = super(SingleTagField, self).widget_attrs(widget)
        attrs.update({
            'data-tag-autocomplete-type': 'single',
        })
        return attrs
        
    def clean(self, value):
        """
        Clean by parsing tag with quotes
        """
        #try:
        #    tags = parse_tags('"%s"' % value, self.tag_options.max_count)
        #    if len(tags) > 0:
        #        value = tags[0]
        #    else:
        #        value = ''
        #except ValueError, e:
        #    raise forms.ValidationError(_('%s' % e))
        tags = super(SingleTagField, self).clean('"%s"' % value)
        if tags:
            return tags[0]
        else:
            return None
        