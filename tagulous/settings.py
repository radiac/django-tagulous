"""
Tagulous default settings

Override these by setting new values in your global settings file
"""

# Path to jQuery >= 1.4.3, for use in the public-facing side of the site
# Relative to STATIC_URL
TAGULOUS_PUBLIC_JQUERY = None
# To use the version of jQuery which is bundled with tagulous, uncomment this:
#TAGULOUS_PUBLIC_JQUERY = 'tagulous/jquery.min.js'

# Path to jQuery => 1.4.3, for use in the admin site
# Relative to STATIC_URL
TAGULOUS_ADMIN_JQUERY = 'tagulous/jquery.min.js'
