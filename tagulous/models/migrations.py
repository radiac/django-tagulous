"""
South migration support
"""
# No unit test coverage of this file - it would be complicated to unit test the
# creation and application of a schema migration, and as South has been
# deprecated it seems like wasted effort. Contributions welcome, but has been
# tested manually instead.

from tagulous import constants
from tagulous.models.models import BaseTagModel, BaseTagTreeModel
from tagulous.models.options import TagOptions
from tagulous.models.fields import SingleTagField, TagField


try:
    from south import modelsinspector
    
    # Monkey-patch South to use BaseTagModel as the base class for tag models
    # in data migrations. It has to use an abstract model without fields,
    # because South adds the fields when it's creating the model, and fields
    # can't be overridden in model subclasses.
    old_get_model_meta = modelsinspector.get_model_meta
    def get_model_meta(model):
        meta_def = old_get_model_meta(model)
        if isinstance(getattr(model, 'tag_options', None), TagOptions):
            if model.tag_options.tree:
                meta_def['_bases'] = ['tagulous.models.BaseTagTreeModel']
            else:
                meta_def['_bases'] = ['tagulous.models.BaseTagModel']
        return meta_def
    modelsinspector.get_model_meta = get_model_meta
    
    
    # Build keyword arguments for south
    south_kwargs = {
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
    
    # Always store _set_tag_meta=True, so migrating tag fields can set tag
    # models' TagMeta during migrations
    south_kwargs['_set_tag_meta'] = [True, {"is_value": True}]
    
    # Add introspection rule for TagField
    modelsinspector.add_introspection_rules([
        (
            [TagField],     # Class(es) these apply to
            [],             # Positional arguments (not used)
            south_kwargs,   # Keyword arguments
        ),
    ], ["^tagulous\.models\.fields\.TagField"])
    
    # Create copy of south_kwargs without max_count
    single_south_kwargs = dict(
        (k, v) for k, v in south_kwargs.items() if k != 'max_count'
    )
    modelsinspector.add_introspection_rules([
        (
            [SingleTagField],     # Class(es) these apply to
            [],                   # Positional arguments (not used)
            single_south_kwargs,  # Keyword arguments
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
        # Make sure tag models won't mess with data during this operation
        is_tag_model = issubclass(model, BaseTagModel)
        for obj in model.objects.all():
            set_fn(obj)
            if is_tag_model:
                obj._save_direct()
            else:   # pragma: no cover - no need, _save_direct() calls save()
                obj.save()
    
    # Change column to unique
    db.alter_column(
        table, column,
        self.gf(field_type)(unique=True, **kwargs)
    )
