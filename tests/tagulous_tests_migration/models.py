"""
Test models
"""

from django.db import models

try:
    import django.apps as django_apps
except ImportError:
    django_apps = None

import tagulous


#
# MigrationTestModel will be created as needed
#

app_name = 'tagulous_tests_migration'


def clear_django():
    "Clear app from django's model cache"
    # Models to clear out from loading cache
    model_names = [
        # Test model
        'migrationtestmodel',
        
        # Tagulous models
        '_tagulous_migrationtestmodel_singletag',
        '_tagulous_migrationtestmodel_tags',
        
        # Django through models
        'migrationtestmodel_tags',
    ]
    
    if django_apps:
        # Django 1.7 or later
        # Clear the get_models LRU cache
        django_apps.apps.clear_cache()
        
        # Find dict container for app models cache
        app_config = django_apps.apps.get_app_config(app_name)
        app_models = app_config.models
        
    else:
        # Django 1.6 or earlier
        # Clear loading cache so they'll be reloaded for next get_models call
        models.loading.cache._get_models_cache.clear()
        
        # Find dict container for app models cache
        app_models = models.loading.cache.app_models.get(app_name, {})
    
    # Clear the named models from the app models cache
    for lower_name in model_names:
        try:
            del app_models[lower_name]
        except KeyError:
            pass

def unset_model():
    "Remove the model"
    if 'MigrationTestModel' in globals():
        del globals()['MigrationTestModel']
    clear_django()

def set_model_initial():
    "Create an initial model without tag fields"
    clear_django()
    return type(
        "MigrationTestModel", (models.Model,), {
            '__module__': 'tests.tagulous_tests_migration.models',
            'name': models.CharField(max_length=10),
        }
    )
    
def set_model_tagged():
    "Initial model with tag fields"
    clear_django()
    model = type(
        "MigrationTestModel", (models.Model,), {
            '__module__': 'tests.tagulous_tests_migration.models',
            'name': models.CharField(max_length=10),
            'singletag': tagulous.models.SingleTagField(blank=True, null=True),
            'tags': tagulous.models.TagField(),
        }
    )
    
    # Just confirm dynamic creation worked as expected
    assert issubclass(model, tagulous.models.tagged.TaggedModel), 'Model is not tagged'
    assert issubclass(model.singletag.tag_model, tagulous.models.models.TagModel), 'Single tag model not TagModel'
    assert issubclass(model.tags.tag_model, tagulous.models.models.TagModel), 'Tag model not TagModel'
    return model
    
def set_model_tree():
    "Tagged model with tags field as tree"
    clear_django()
    model = type(
        "MigrationTestModel", (models.Model,), {
            '__module__': 'tests.tagulous_tests_migration.models',
            'name': models.CharField(max_length=10),
            'singletag': tagulous.models.SingleTagField(blank=True, null=True),
            'tags': tagulous.models.TagField(tree=True),
        }
    )

    # Just confirm dynamic creation worked as expected
    assert issubclass(model, tagulous.models.tagged.TaggedModel), 'Model is not tagged'
    assert issubclass(model.singletag.tag_model, tagulous.models.models.TagModel), 'Single tag model not TagModel'
    assert issubclass(model.tags.tag_model, tagulous.models.models.TagModel), 'Tag model not TagModel'
    return model
