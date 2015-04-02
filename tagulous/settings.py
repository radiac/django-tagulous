"""
Tagulous default settings

Override these by setting new values in your global settings file
"""
from django.conf import settings

from tagulous import constants


AUTOCOMPLETE_JS = getattr(
    settings, 'TAGULOUS_AUTOCOMPLETE_JS', (
        constants.PATH_JQUERY,
        constants.PATH_TAGULOUS_JS,
        constants.PATH_SELECT2_JS,
        constants.PATH_SELECT2_ADAPTOR,
    )
)
AUTOCOMPLETE_CSS = getattr(
    settings, 'TAGULOUS_AUTOCOMPLETE_CSS', {
        'all':  [constants.PATH_SELECT2_CSS],
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

# Option to disable the add related widget in auto-generated admin fields.
#
# If the tag model is registered with the admin site, without this setting
# the model admin will automatically add a "+" button next to the tag field.
# This will not function correctly, so if you do register the tag model, you
# should set this to True.
#
# This will monkey-patch BaseModelAdmin.formfield_for_dbfield to not add
# a RelatedFieldWidgetWrapper to a TagWidget or SingleTagWidget. Even though
# it should not cause any problems, it is off by default, just in case.
DISABLE_ADMIN_ADD = getattr(settings, 'TAGULOUS_DISABLE_ADMIN_ADD', False)
