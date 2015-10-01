"""
Tagulous default settings

Override these by setting new values in your global settings file
"""
from __future__ import unicode_literals

from django.conf import settings
from django.utils import six


#
# Autocomplete settings
#

AUTOCOMPLETE_JS = getattr(
    settings, 'TAGULOUS_AUTOCOMPLETE_JS', (
        'tagulous/lib/jquery.js',
        'tagulous/lib/select2-3/select2.min.js',
        'tagulous/tagulous.js',
        'tagulous/adaptor/select2-3.js',
    )
)
AUTOCOMPLETE_CSS = getattr(
    settings, 'TAGULOUS_AUTOCOMPLETE_CSS', {
        'all':  ['tagulous/lib/select2-3/select2.css'],
    }
)
AUTOCOMPLETE_SETTINGS = getattr(
    settings, 'TAGULOUS_AUTOCOMPLETE_SETTINGS', None
)

# Admin overrides
ADMIN_AUTOCOMPLETE_JS = getattr(
    settings, 'TAGULOUS_ADMIN_AUTOCOMPLETE_JS', AUTOCOMPLETE_JS
)
ADMIN_AUTOCOMPLETE_CSS = getattr(
    settings, 'TAGULOUS_ADMIN_AUTOCOMPLETE_CSS', AUTOCOMPLETE_CSS
)
ADMIN_AUTOCOMPLETE_SETTINGS = getattr(
    settings, 'TAGULOUS_ADMIN_AUTOCOMPLETE_SETTINGS', AUTOCOMPLETE_SETTINGS
)


#
# Tag weighting defaults, for tag model queryset .weight() method
#

WEIGHT_MIN = getattr(settings, 'TAGULOUS_WEIGHT_MIN', 1)
WEIGHT_MAX = getattr(settings, 'TAGULOUS_WEIGHT_MAX', 6)


#
# Feature flags
#

# Option to automatically enhance Model, Manager and QuerySet classes so they
# know how to work with SingleTagFields and TagFields.
#
# This will automatically change models which use tag fields to subclass
# TaggedModel, their managers to subclass TaggedManager, and their querysets to
# subclass TaggedQuerySet
#
# If this is set to False, certain aspects of tag fields will not work as
# expected; you should consider manually subclassing the relevant classes.
# See settings documentation for more information.
ENHANCE_MODELS = getattr(settings, 'TAGULOUS_ENHANCE_MODELS', True)
