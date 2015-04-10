"""
South migration support
"""

from tagulous import constants
from tagulous.models.options import TagOptions
from tagulous.models.fields import SingleTagField, TagField


try:
    from south import modelsinspector
    
    # Monkey-patch South to use TagModel as the base class for tag models
    # This will allow Tagulous to work in data migrations
    old_get_model_meta = modelsinspector.get_model_meta
    def get_model_meta(model):
        meta_def = old_get_model_meta(model)
        if isinstance(getattr(model, 'tag_options', None), TagOptions):
            meta_def['_bases'] = ['tagulous.models.BaseTagModel']
        return meta_def
    modelsinspector.get_model_meta = get_model_meta
    
    
    # Build keyword arguments for south
    south_kwargs = {
        # Don't want the tag model if it is generated automatically
        #'tag_model':    ['tag_model', {'ignore_if': 'auto_tag_model'}],
        
        # Never want
        #'to':           ['south_supression', {'ignore_if': 'south_supression'}],
        
        # Never want fk
        'to_field':     ['south_supression', {'ignore_if': 'south_supression'}],
        'rel_class':    ['south_supression', {'ignore_if': 'south_supression'}],
        
        # Never want m2m
        'db_table':     ['south_supression', {'ignore_if': 'south_supression'}],
        'through':      ['south_supression', {'ignore_if': 'south_supression'}],
        'symmetrical':  ['south_supression', {'ignore_if': 'south_supression'}],
    }
    
    # Add tag options
    for key, value in constants.OPTION_DEFAULTS.items():
        seek = key
        if key == 'initial':
            seek = 'initial_string'
        south_kwargs[key] = ['tag_options.%s' % seek, {'default':value}]
    
    # Add introspection rule for TagField
    modelsinspector.add_introspection_rules([
        (
            [TagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.TagField"])
    
    # No max_count for SingleTagField
    del(south_kwargs['max_count'])
    modelsinspector.add_introspection_rules([
        (
            [SingleTagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.SingleTagField"])
    
except ImportError, e:
    # South not installed
    pass
