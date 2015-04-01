
#
# Tag options
#

class TagOptions(object):
    """
    Simple class container for tag options
    """
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
    
    def _set_initial(self, value):
        if isinstance(value, basestring):
            self.initial_string = value
            self._initial = parse_tags(value)
        else:
            self.initial_string = edit_string_for_tags(value)
            self._initial = value
    initial = property(lambda self: self._initial, _set_initial)
    
    def items(self):
        """
        Get a dict of all options
        """
        return dict([ (opt, getattr(self, opt)) for opt in OPTION_DEFAULTS ])
            
    def field_items(self):
        """
        Get a dict of all options except those in EXCLUDE_FIELD_OPTIONS
        """
        return dict([
            (opt, getattr(self, opt)) for opt in [
                key for key in OPTION_DEFAULTS.keys()
                if key not in EXCLUDE_FIELD_OPTIONS
            ]
        ])
