"""
Migration support for South and Django migrations
"""
from __future__ import unicode_literals

from tagulous import constants
from tagulous import settings
from tagulous.models.models import BaseTagModel, BaseTagTreeModel
from tagulous.models.tagged import TaggedModel
from tagulous.models.options import TagOptions
from tagulous.models.fields import SingleTagField, TagField
from django.utils import six


###############################################################################
############################################################ Django migrations
###############################################################################

# Check for migration frameworks
try:
    from django.db import migrations as django_migrations
except ImportError:
    # Django migrations not available
    django_migrations = None


def django_support():
    from django.db.migrations import state
    
    # Monkey-patch Django so it doesn't flatten TagModel abstract base classes.
    # We need them so the BaseTagModel metaclass can set up its options, and
    # so that tag model functionality is available in migrations.
    old_from_model = state.ModelState.from_model.__func__
    def from_model(cls, model, exclude_rels=False):
        base = None
        if issubclass(model, BaseTagTreeModel):
            base = BaseTagTreeModel
        elif issubclass(model, BaseTagModel):
            base = BaseTagModel
            
        modelstate = old_from_model(cls, model, exclude_rels)
        
        if base is not None:
            modelstate.bases = (base,) + modelstate.bases
        return modelstate
    state.ModelState.from_model = classmethod(from_model)


# Add Tagulous support to Django migrations if available
if django_migrations is not None:
    django_support()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Helpers for Django migrations
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if django_migrations is not None:
    class ChangeModelBases(django_migrations.operations.base.Operation):
        """
        Change a Model's bases so it is correct for data migrations
        """
        def __init__(self, name, bases):
            self.name = name
            self.bases = bases
        
        def state_forwards(self, app_label, state):
            state.models[app_label, self.name.lower()].bases = self.bases
        
        def database_forwards(self, *args, **kwargs):
            pass
        def database_backwards(self, *args, **kwargs):
            pass


def add_unique_field(model_name, name, field, preserve_default, set_fn):
    """
    Helper for Django migrations which returns a list of Operations to add a
    unique field.
    
    Warning: only use on a database which supports transactions, in case your
    set_fn method fails and leaves your database in an unusable state.
    
    Create a migration and provide the string 'x' as the default when prompted.
    
    Then find the field definition in your migration and replace it with a call
    to this function, removing the default:
    
        operations = [
            migrations.AddField(
                ...
            ),
            migrations.AddField(
                model_name='mymodel',
                name='my_column',
                field=models.TextField(default='x', unique=True),
                preserve_default=False,
            ),
            migrations.AddField(
                ...
            ),
        ]
    
    becomes:
        
        def set_new_column(obj):
            obj.new_column = slugify(obj.name)
        
        operations = [
            migrations.AddField(
                ...
            ),
        ] + tagulous.models.migration.add_unique_field(
            model_name='mymodel',
            name='my_column',
            field=models.TextField(unique=True),
            preserve_default=False,
            set_fn=set_new_column,
        ) + [
            migrations.AddField(
                ...
            ),
        ]
    
    Arguments:
        model_name  As django defines
        name        As django defines
        field       As django defines, but without default
        preserve_default    As django defines
        set_fn      Callback to set the field on each instance
    """
    if django_migrations is None: # pragma: no cover
        raise ValueError('Cannot use add_unique_column without Django migrations')
    
    # Clone the field so it's not unique and can be null
    field_nullable = field.clone()
    field_nullable._unique = False
    field_nullable.null = True
    
    # RunPython doesn't give the code the app label; pass it as an attribute
    # to save users having to specify the app
    class RunPythonWithAppLabel(django_migrations.RunPython):
        def database_forwards(self, app_label, *args, **kwargs):
            self.code.app_label = app_label
            super(RunPythonWithAppLabel, self).database_forwards(
                app_label, *args, **kwargs
            )
        
        def database_backwards(self, app_label, *args, **kwargs):
            self.code.app_label = app_label
            super(RunPythonWithAppLabel, self).database_backwards(
                app_label, *args, **kwargs
            )
    
    # Function to generate the unique value
    def set_unique_values(apps, schema_editor):
        model = apps.get_model(set_unique_values.app_label, model_name)
        
        # Make sure tag models won't mess with data during this operation
        is_tag_model = issubclass(model, BaseTagModel)
        for obj in model.objects.all():
            set_fn(obj)
            if is_tag_model:
                obj._save_direct()
            else:   # pragma: no cover - no need, _save_direct() calls save()
                obj.save()
    
    return [
        django_migrations.AddField(
            model_name=model_name,
            name=name,
            field=field_nullable,
            preserve_default=preserve_default,
        ),
        RunPythonWithAppLabel(
            set_unique_values,
            reverse_code=lambda *a, **k: None
        ),
        django_migrations.AlterField(
            model_name=model_name,
            name=name,
            field=field,
            preserve_default=preserve_default,
        ),
    ]


###############################################################################
############################################################ South migrations
###############################################################################

try:
    import south
except ImportError:
    # South not installed
    south = None
    
def south_support():
    from south import modelsinspector
    from south import orm
    
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
    
    # Monkey-patch South to make sure tagged models subclass TaggedModel.
    # It should happen automatically, and will most of the time - but because
    # South doesn't guarantee order fields are created, it can fail to create
    # ForeignKey and ManyToManyField fields the first time. When that happens
    # it goes back and adds them later - but by then the class_prepared signal
    # will have fired, and we may have missed the tag fields. Therefore we have
    # to re-examine all modules South creates after it has fixed failed fields.
    if settings.ENHANCE_MODELS:
        old_retry_failed_fields = orm._FakeORM.retry_failed_fields
        def retry_failed_fields(self):
            old_retry_failed_fields(self)
            for modelkey, model in self.models.items():
                TaggedModel.cast_class(model)
        orm._FakeORM.retry_failed_fields = retry_failed_fields
    
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
    

# Add Tagulous support to South migrations, if available
if south is not None:
    south_support()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Helpers for South
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def add_unique_column(self, db, model, column, set_fn, field_type, **kwargs):
    """
    Helper for South migrations which add a unique field.
    
    Warning: only use on a database which supports transactions, in case your
    set_fn method fails and leaves your database in an unusable state.
    
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
    if south is None: # pragma: no cover
        raise ValueError('Cannot use add_unique_column without south')
    
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


