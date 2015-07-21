"""
Test models
"""

from django.db import models

import tagulous


#
# MigrationTestModel will be created as needed
#

app_name = 'tagulous_tests_migration'


def clear_django():
    "Clear app from django's model cache"
    # Clean out models from loading cache
    for lower_name in [
        # Test model
        'migrationtestmodel',
        
        # Tagulous models
        '_tagulous_migrationtestmodel_singletag',
        '_tagulous_migrationtestmodel_tags',
        
        # Django through models
        'migrationtestmodel_tags',
    ]:
        try:
            del models.loading.cache.app_models[app_name][lower_name]
        except KeyError:
            pass
    
    # Clear other loading cache so they'll be reloaded for next get_models call
    models.loading.cache._get_models_cache.clear()
    
    
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
            '__module__': 'tagulous.tests.tagulous_tests_migration.models',
            'name': models.CharField(max_length=10),
        }
    )
    
def set_model_tagged():
    "Initial model with tag fields"
    clear_django()
    model = type(
        "MigrationTestModel", (models.Model,), {
            '__module__': 'tagulous.tests.tagulous_tests_migration.models',
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
    return type(
        "MigrationTestModel", (models.Model,), {
            '__module__': 'tagulous.tests.tagulous_tests_migration.models',
            'name': models.CharField(max_length=10),
            'singletag': tagulous.models.SingleTagField(blank=True, null=True),
            'tags': tagulous.models.TagField(tree=True),
        }
    )
