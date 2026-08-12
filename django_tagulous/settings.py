"""
Tagulous default settings

Override these by setting new values in your global settings file
"""

import warnings

from django.conf import settings

from .constants import (
    AUTOCOMPLETE_CSS_DROPULOUS,
    AUTOCOMPLETE_CSS_SELECT2,
    AUTOCOMPLETE_JS_DROPULOUS,
    AUTOCOMPLETE_JS_SELECT2,
    OPTION_DEFAULTS,
)

#
# Database control settings
#

NAME_MAX_LENGTH = getattr(settings, "TAGULOUS_NAME_MAX_LENGTH", 255)
SLUG_MAX_LENGTH = getattr(settings, "TAGULOUS_SLUG_MAX_LENGTH", 50)
LABEL_MAX_LENGTH = getattr(settings, "TAGULOUS_LABEL_MAX_LENGTH", NAME_MAX_LENGTH)

# Number of characters to allow for finding a unique slug, ie if set to 5, the
# slug will be truncated by up to 5 characters to allow for a suffix of _9999
SLUG_TRUNCATE_UNIQUE = getattr(settings, "TAGULOUS_SLUG_TRUNCATE_UNIQUE", 5)

# Set to false to generate ASCII slugs
SLUG_ALLOW_UNICODE = getattr(settings, "TAGULOUS_SLUG_ALLOW_UNICODE", False)


#
# Field settings
#

# Collect dict of default values, and use them to override the internal defaults
# Validate them against the internal defaults, as TagOptions would
DEFAULT_TAG_OPTIONS = {
    **OPTION_DEFAULTS,
    **getattr(settings, "TAGULOUS_DEFAULT_TAG_OPTIONS", {}),
}
if _unknown := set(DEFAULT_TAG_OPTIONS) - set(OPTION_DEFAULTS):
    raise ValueError(f"Unexpected TAGULOUS_DEFAULT_TAG_OPTIONS: {', '.join(_unknown)}")


#
# Autocomplete settings
#

# In v3 we're swapping to Dropulous as the default for public forms
# This temporary transition setting will give people an easy way to try it now, or
# at least the warning will prompt them to force to select2 to avoid a surprise in v3.
TRANSITION_DROPULOUS = getattr(settings, "TAGULOUS_TRANSITION_DROPULOUS", False)
if TRANSITION_DROPULOUS:
    DEFAULT_AUTOCOMPLETE_JS = AUTOCOMPLETE_JS_DROPULOUS
    DEFAULT_AUTOCOMPLETE_CSS = AUTOCOMPLETE_CSS_DROPULOUS
else:
    DEFAULT_AUTOCOMPLETE_JS = AUTOCOMPLETE_JS_SELECT2
    DEFAULT_AUTOCOMPLETE_CSS = AUTOCOMPLETE_CSS_SELECT2
    if not hasattr(settings, "TAGULOUS_AUTOCOMPLETE_JS"):
        warnings.warn(
            "Tagulous will switch from select2 to dropulous as its default public"
            " autocomplete library in v3.0.0. You should decide which to use - see"
            " upgrade docs for details.",
            DeprecationWarning,
            stacklevel=2,
        )

AUTOCOMPLETE_JS = getattr(settings, "TAGULOUS_AUTOCOMPLETE_JS", DEFAULT_AUTOCOMPLETE_JS)
AUTOCOMPLETE_CSS = getattr(
    settings, "TAGULOUS_AUTOCOMPLETE_CSS", DEFAULT_AUTOCOMPLETE_CSS
)
AUTOCOMPLETE_SETTINGS = getattr(settings, "TAGULOUS_AUTOCOMPLETE_SETTINGS", None)

# We won't use dropulous in admin - there's no advantage over Django's vendored select2
DEFAULT_ADMIN_AUTOCOMPLETE_JS = (
    "tagulous/tagulous.js",
    "tagulous/adaptor/select2-4.js",
)
DEFAULT_ADMIN_AUTOCOMPLETE_CSS = {}

ADMIN_AUTOCOMPLETE_JS = getattr(
    settings, "TAGULOUS_ADMIN_AUTOCOMPLETE_JS", DEFAULT_ADMIN_AUTOCOMPLETE_JS
)
ADMIN_AUTOCOMPLETE_CSS = getattr(
    settings, "TAGULOUS_ADMIN_AUTOCOMPLETE_CSS", DEFAULT_ADMIN_AUTOCOMPLETE_CSS
)
ADMIN_AUTOCOMPLETE_SETTINGS = getattr(
    settings, "TAGULOUS_ADMIN_AUTOCOMPLETE_SETTINGS", AUTOCOMPLETE_SETTINGS
)


#
# Tag weighting defaults, for tag model queryset .weight() method
#

WEIGHT_MIN = getattr(settings, "TAGULOUS_WEIGHT_MIN", 1)
WEIGHT_MAX = getattr(settings, "TAGULOUS_WEIGHT_MAX", 6)


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
_enhance_default = True
if hasattr(settings, "TAGULOUS_ENHANCE_MODELS"):
    import warnings

    warnings.warn(
        "TAGULOUS_ENHANCE_MODELS is deprecated, use TAGULOUS_ENHANCE instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    _enhance_default = settings.TAGULOUS_ENHANCE_MODELS
ENHANCE = getattr(settings, "TAGULOUS_ENHANCE", _enhance_default)
