"""
Tagulous constants
"""

#
# Static file paths (relative to STATIC_URL)
#

# Path to version of jQuery included with tagulous
PATH_JQUERY = 'tagulous/lib/jquery-1.11.2.min.js'

# Path to tagulous library code, for window.Tagulous
PATH_TAGULOUS_JS = 'tagulous/tagulous.js'

# Paths to version of Select2 included with tagulous
PATH_SELECT2_JS = 'tagulous/lib/select2-3.5.2/select2.min.js'
PATH_SELECT2_CSS = 'tagulous/lib/select2-3.5.2/select2.css'

# Paths to adaptors
PATH_SELECT2_ADAPTOR = 'tagulous/adaptor/select2.js'


#
# Model constants
#

MODEL_PREFIX = '_Tagulous'

# Default model TagField options
OPTION_DEFAULTS = {
    'protect_all':      False,
    'initial':          '',
    'protect_initial':  True,
    'case_sensitive':   False,
    'force_lowercase':  False,
    'max_count':        0,
    'autocomplete_view':    '',
    'autocomplete_limit':   100,
    'autocomplete_settings': None
}

# List of model TagField options which are relevant to client-side code
FIELD_OPTIONS = [
    'case_sensitive',
    'force_lowercase',
    'max_count',
    'autocomplete_limit',
    'autocomplete_settings'
]
