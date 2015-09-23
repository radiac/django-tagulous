# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

import tagulous


class Migration(DataMigration):
    #
    # Implement basic unittest-esque methods
    #
    
    def fail(self, msg):
        # Fail loudly so the message can be picked up by the calling test
        raise AssertionError(msg)
    
    def assertEqual(self, a, b):
        if a != b:
            self.fail("%r != %r" % (a, b))
    
    def assertIsSubclass(self, cls, supercls):
        if not issubclass(cls, supercls):
            self.fail("%r is not a subclass of %r: %s" % (cls, supercls, cls.__bases__))
    
    def assertIsInstance(self, obj, cls, msg=None):
        if not isinstance(obj, cls):
            self.fail("%r is not an instance of %r" % (obj, cls))
    
    
    #
    # Perform tests
    #
    
    def forwards(self, orm):
        "Test that Tagulous works in data migrations"
        # Find tagged model
        model = orm['tagulous_tests_migration.MigrationTestModel']
        
        # Check classes have been assigned correctly
        # If so, everything else will work as it should
        self.assertIsSubclass(model, tagulous.models.TaggedModel)
        
        self.assertIsInstance(
            model.singletag, tagulous.models.SingleTagDescriptor
        )
        self.assertIsSubclass(
            model.singletag.tag_model, tagulous.models.BaseTagModel
        )
        
        self.assertIsInstance(
            model.tags, tagulous.models.TagDescriptor
        )
        self.assertIsSubclass(
            model.tags.tag_model, tagulous.models.BaseTagTreeModel
        )
        

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'tagulous_tests_migration._tagulous_migrationtestmodel_singletag': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('slug',),)", 'object_name': '_Tagulous_MigrationTestModel_singletag', '_bases': ['tagulous.models.BaseTagModel']},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'protected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'tagulous_tests_migration._tagulous_migrationtestmodel_tags': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('slug', 'parent'),)", 'object_name': '_Tagulous_MigrationTestModel_tags', '_bases': ['tagulous.models.BaseTagTreeModel']},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['tagulous_tests_migration._Tagulous_MigrationTestModel_tags']"}),
            'path': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'protected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'tagulous_tests_migration.migrationtestmodel': {
            'Meta': {'object_name': 'MigrationTestModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'singletag': ('tagulous.models.fields.SingleTagField', [], {'_set_tag_meta': 'True', 'blank': 'True', 'to': u"orm['tagulous_tests_migration._Tagulous_MigrationTestModel_singletag']", 'null': 'True'}),
            'tags': ('tagulous.models.fields.TagField', [], {'to': u"orm['tagulous_tests_migration._Tagulous_MigrationTestModel_tags']", 'tree': 'True', '_set_tag_meta': 'True'})
        }
    }

    complete_apps = ['tagulous_tests_migration']
    symmetrical = True
