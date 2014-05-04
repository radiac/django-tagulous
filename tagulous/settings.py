"""
Tagulous default settings

Override these by setting new values in your global settings file
"""
from django.conf import settings

# Path to jQuery >= 1.4.3, for use in the public-facing side of the site
# Relative to STATIC_URL
# Default: use the version of jQuery which is bundled with tagulous
# Set to False to disable
PUBLIC_JQUERY = getattr(
    settings, 'TAGULOUS_PUBLIC_JQUERY', 'tagulous/jquery-1.10.2.min.js',
)

# Path to jQuery => 1.4.3, for use in the admin site
# Relative to STATIC_URL
# Default: use the version of jQuery which is bundled with tagulous
# Set to False to disable
ADMIN_JQUERY = getattr(
    settings, 'TAGULOUS_ADMIN_JQUERY', 'tagulous/jquery-1.10.2.min.js',
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
