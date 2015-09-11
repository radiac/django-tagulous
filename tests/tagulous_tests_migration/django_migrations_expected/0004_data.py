# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tagulous.models


#
# Basic unittest-esque functions
#
    
def fail(msg):
    # Fail loudly so the message can be picked up by the calling test
    raise AssertionError(msg)

def assertEqual( a, b):
    if a != b:
        fail("%r != %r" % (a, b))

def assertIsSubclass(cls, supercls):
    if not issubclass(cls, supercls):
        fail("%r is not a subclass of %r: %s" % (cls, supercls, cls.__bases__))

def assertIsInstance(obj, cls, msg=None):
    if not isinstance(obj, cls):
        fail("%r is not an instance of %r" % (obj, cls))


#
# Migration
# 

def test_tagulous_in_migrations(apps, schema_editor):
    "Test that Tagulous works in data migrations"
    # Find tagged model
    model = apps.get_model('tagulous_tests_migration', 'MigrationTestModel')
    
    # Check classes have been assigned correctly
    # If so, everything else will work as it should
    assertIsSubclass(model, tagulous.models.TaggedModel)
    
    assertIsInstance(
        model.singletag, tagulous.models.SingleTagDescriptor
    )
    assertIsSubclass(
        model.singletag.tag_model, tagulous.models.BaseTagModel
    )
    
    assertIsInstance(
        model.tags, tagulous.models.TagDescriptor
    )
    assertIsSubclass(
        model.tags.tag_model, tagulous.models.BaseTagTreeModel
    )
        

class Migration(migrations.Migration):

    dependencies = [
        ('tagulous_tests_migration', '0003_tree'),
    ]
    
    operations = [
        migrations.RunPython(test_tagulous_in_migrations, lambda *a, **k: None)
    ]
