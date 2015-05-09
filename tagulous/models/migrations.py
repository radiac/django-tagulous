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
        
        # Store initial as a string
        if key == 'initial':
            seek = 'initial_string'
            
        # Can't freeze callables - don't need to anyway
        if key == 'get_absolute_url':
            continue
            
        south_kwargs[key] = ['tag_options.%s' % seek, {'default': value}]
    
    # Add introspection rule for TagField
    modelsinspector.add_introspection_rules([
        (
            [TagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.fields\.TagField"])
    
    # No max_count for SingleTagField
    del(south_kwargs['max_count'])
    modelsinspector.add_introspection_rules([
        (
            [SingleTagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.fields\.SingleTagField"])
    
except ImportError, e:
    # South not installed
    pass



def add_unique_column(self, db, model, column, set_fn, field_type, **kwargs):
    """
    Helper for South migrations which add a unique field.
    
    This must be the last operation on this table in this migration, otherwise
    when it tries to load data, the orm will not match the database.
    
    Find the field definition in your migration and replace it with a call to
    this function:
    
        db.add_column(
            'my_table', 'my_column',
            self.gf(
                'django.db.models.fields.CharField'
            )(default='.', unique=True, max_length=255),
            keep_default=False
        )
    
    becomes:
        
        def set_new_column(obj):
            obj.new_column = slugify(obj.name)
        
        tagulous.models.migrations.add_unique_column(
            self, db, orm['myapp.MyModel'], 'new_column', set_new_column,
            'django.db.models.fields.CharField',
            max_length=255
        )
    
    Arguments:
        self        Migration object
        db          db object
        model       Model (from orm)
        column      Name of db column to add
        set_fn      Callback to set the field on each instance
        field_type  String reference to Field object
        **kwargs    Arguments for Field object, excluding unique
    """
    table = model._meta.db_table
    
    # Create the column as non-unique
    initial = kwargs.copy()
    initial.update({
        'blank':    True,
        'null':     True,
        'unique':   False,
    })
    db.add_column(
        table, column,
        self.gf(field_type)(**initial),
        keep_default=False
    )
    
    # Set the fields
    if not db.dry_run:
        for obj in model.objects.all():
            set_fn(obj)
            obj.save()
    
    # Change column to unique
    db.alter_column(
        table, column,
        self.gf(field_type)(unique=True, **kwargs)
    )
