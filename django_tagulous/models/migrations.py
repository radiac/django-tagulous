"""
Migration support for Django migrations
"""

from django.db import migrations

from .models import BaseTagModel, BaseTagTreeModel

# ##############################################################################
# ########################################################### Django migrations
# ##############################################################################


def django_support():
    # Monkey-patch Django so it doesn't flatten TagModel abstract base classes.
    # We need them so the BaseTagModel metaclass can set up its options, and
    # so that tag model functionality is available in migrations.
    old_from_model = migrations.state.ModelState.from_model.__func__

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

    migrations.state.ModelState.from_model = classmethod(from_model)


# Add Tagulous support to Django migrations
django_support()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#       Helpers for Django migrations
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class ChangeModelBases(migrations.operations.base.Operation):
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
    if migrations is None:  # pragma: no cover
        raise ValueError("Cannot use add_unique_column without Django migrations")

    # Clone the field so it's not unique and can be null
    field_nullable = field.clone()
    field_nullable._unique = False
    field_nullable.null = True

    # RunPython doesn't give the code the app label; pass it as an attribute
    # to save users having to specify the app
    class RunPythonWithAppLabel(migrations.RunPython):
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
            else:  # pragma: no cover - no need, _save_direct() calls save()
                obj.save()

    return [
        migrations.AddField(
            model_name=model_name,
            name=name,
            field=field_nullable,
            preserve_default=preserve_default,
        ),
        RunPythonWithAppLabel(set_unique_values, reverse_code=lambda *a, **k: None),
        migrations.AlterField(
            model_name=model_name,
            name=name,
            field=field,
            preserve_default=preserve_default,
        ),
    ]
