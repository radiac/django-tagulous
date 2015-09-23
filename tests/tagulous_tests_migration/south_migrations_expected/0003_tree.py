# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on '_Tagulous_MigrationTestModel_tags', fields ['slug']
        db.delete_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', ['slug'])
        # Adding field '_Tagulous_MigrationTestModel_tags.parent'
        db.add_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'parent',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['tagulous_tests_migration._Tagulous_MigrationTestModel_tags']),
                      keep_default=False)

        # Adding field '_Tagulous_MigrationTestModel_tags.label'
        db.add_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'label',
                      self.gf('django.db.models.fields.CharField')(default='.', max_length=255),
                      keep_default=False)

        # Adding field '_Tagulous_MigrationTestModel_tags.level'
        db.add_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'level',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field '_Tagulous_MigrationTestModel_tags.path'
        from tagulous.models.migrations import add_unique_column
        add_unique_column(
            self, db,
            orm['tagulous_tests_migration._Tagulous_MigrationTestModel_tags'],
            'path',
            lambda obj: setattr(obj, 'path', str(obj.pk)),
            'django.db.models.fields.TextField',
        )
        
        # Adding unique constraint on '_Tagulous_MigrationTestModel_tags', fields ['slug', 'parent']
        db.create_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', ['slug', 'parent_id'])


    def backwards(self, orm):
        # Removing unique constraint on '_Tagulous_MigrationTestModel_tags', fields ['slug', 'parent']
        db.delete_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', ['slug', 'parent_id'])

        # Deleting field '_Tagulous_MigrationTestModel_tags.parent'
        db.delete_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'parent_id')

        # Deleting field '_Tagulous_MigrationTestModel_tags.path'
        db.delete_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'path')
        
        # Deleting field 'BookmarkTag.label'
        db.delete_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'label')

        # Deleting field 'BookmarkTag.level'
        db.delete_column(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', 'level')

        # Adding unique constraint on '_Tagulous_MigrationTestModel_tags', fields ['slug']
        db.create_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', ['slug'])


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