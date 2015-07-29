from django import forms
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import EMPTY_VALUES
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.encoding import force_unicode

# ++ Can remove this try/except when min req is Django 1.5
try:
    import json
except ImportError: # pragma: no cover
   from django.utils import simplejson as json

from tagulous import settings
from tagulous.models import options
from tagulous.models.models import BaseTagModel, TagModelQuerySet
from tagulous.utils import parse_tags, render_tags


class TagWidgetBase(forms.TextInput):
    """
    Base class for tag widgets
    """
    # Attributes that subclasses must set
    autocomplete_settings = None
    
    # Attributes that the calling Field must set
    tag_options = None
    autocomplete_tags = None
    
    # Provide choices attribute for admin site, to avoid an error in the event
    # tagulous.admin isn't used to register the admin model
    choices = None
    
    def render(self, name, value, attrs={}):
        # Try to provide a URL for the autocomplete to load tags on demand
        autocomplete_view = self.tag_options.autocomplete_view
        if autocomplete_view:
            try:
                attrs['data-tag-url'] = reverse(autocomplete_view)
            except NoReverseMatch, e:
                raise ValueError('Invalid autocomplete view: %s' % e)
        
        # Otherwise embed them, if provided
        elif self.autocomplete_tags is not None:
            autocomplete_tags = self.autocomplete_tags
            # If it's a queryset, make sure it hasn't been consumed, otherwise
            # changes won't show in the list
            if isinstance(autocomplete_tags, QuerySet):
                autocomplete_tags = autocomplete_tags.all()
            
            attrs['data-tag-list'] = escape(force_unicode(
                json.dumps(
                    # Call __unicode__ rather than tag.name directly, in case
                    # we've been given a list of tag strings
                    [unicode(tag) for tag in autocomplete_tags],
                    cls=DjangoJSONEncoder,
                ),
            ))
        
        # Merge default autocomplete settings into tag options
        tag_options = self.tag_options.field_items(with_defaults=False)
        if self.default_autocomplete_settings is not None:
            autocomplete_settings = self.default_autocomplete_settings.copy()
            autocomplete_settings.update(
                tag_options.get('autocomplete_settings', {})
            )
            tag_options['autocomplete_settings'] = autocomplete_settings
        
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


class BaseTagField(forms.CharField):
    """
    Base class for form tag fields
    """
    # Use the tag widget
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
        super(BaseTagField, self).__init__(**kwargs)
        
        # Add tag options and autocomplete tags
        # Will use getters and setters to mirror onto widget
        self.tag_options = tag_options or options.TagOptions()
        self.autocomplete_tags = autocomplete_tags
        
    def prepare_value(self, value):
        """
        Prepare the value - a tag string
        """
        # Catch no value (empty form for add)
        if not value:
            tag_string = ''
            
        # Will normally get a string
        elif isinstance(value, basestring):
            tag_string = value
        
        # Otherwise we have an invalid value
        else:
            raise ValueError(_("Tag field could not prepare unexpected value"))
            
        return super(BaseTagField, self).prepare_value(tag_string)
    
    # Use setters and getters to ensure any changes to the field are mirrored
    # in the widget, in the same way ModelChoiceField mirrors its queryset
    def _get_tag_options(self):
        return self._tag_options
    def _prepare_tag_options(self, tag_options):
        "Clone tag options"
        return tag_options + options.TagOptions()
    def _set_tag_options(self, tag_options):
        tag_options = self._prepare_tag_options(tag_options)
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
        
    def clean(self, value, single=False):
        """
        Clean the form value
        
        If optional argument ``single`` is True, the returned value will be a
        string containing the tag name.
        
        If ``single`` is False (default), the returned value will be a list of
        strings containing tag names.
        """
        value = super(BaseTagField, self).clean(value)
        
        if self.tag_options.force_lowercase:
            value = value.lower()
        
        if single:
            return value
        
        try:
            return parse_tags(value, self.tag_options.max_count)
        except ValueError, e:
            raise forms.ValidationError(_('%s' % e))
        

class SingleTagField(BaseTagField):
    """
    Single tag field
    
    For parsing purposes, a single tag field wraps the contents in quotes
    """
    def prepare_value(self, value):
        """
        Prepare the value by stripping quotes
        """
        # Might have been passed a Tag object via initial - convert to string
        if isinstance(value, BaseTagModel):
            value = value.name
        tag_string = value
        return super(SingleTagField, self).prepare_value(tag_string)
      
    def _prepare_tag_options(self, tag_options):
        """
        Force max_count to 1
        """
        return tag_options + options.TagOptions(
            max_count=1,
        )
        
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
        tag = super(SingleTagField, self).clean(value, single=True)
        if tag:
            return tag
        else:
            return None


class TagField(BaseTagField):
    """
    Form tag field
    """
    def prepare_value(self, value):
        """
        Prepare the value
        """
        # Could receive iterable of tags from a form's initial object
        if (
            isinstance(value, TagModelQuerySet)
            or (
                hasattr(value, '__getitem__')
                and all(isinstance(tag, BaseTagModel) for tag in value)
            )
        ):
            value = render_tags(value)
        
        # Deal with it as normal
        return super(TagField, self).prepare_value(value)
