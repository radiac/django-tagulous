# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model '_Tagulous_MigrationTestModel_tags'
        db.create_table(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('protected', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'tagulous_tests_migration', ['_Tagulous_MigrationTestModel_tags'])

        # Adding unique constraint on '_Tagulous_MigrationTestModel_tags', fields ['slug']
        db.create_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', ['slug'])

        # Adding model '_Tagulous_MigrationTestModel_singletag'
        db.create_table(u'tagulous_tests_migration__tagulous_migrationtestmodel_singletag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('protected', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'tagulous_tests_migration', ['_Tagulous_MigrationTestModel_singletag'])

        # Adding unique constraint on '_Tagulous_MigrationTestModel_singletag', fields ['slug']
        db.create_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_singletag', ['slug'])

        # Adding field 'MigrationTestModel.singletag'
        db.add_column(u'tagulous_tests_migration_migrationtestmodel', 'singletag',
                      self.gf('tagulous.models.fields.SingleTagField')(_set_tag_meta=True, null=True, to=orm['tagulous_tests_migration._Tagulous_MigrationTestModel_singletag'], blank=True),
                      keep_default=False)

        # Adding M2M table for field tags on 'MigrationTestModel'
        m2m_table_name = db.shorten_name(u'tagulous_tests_migration_migrationtestmodel_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('migrationtestmodel', models.ForeignKey(orm[u'tagulous_tests_migration.migrationtestmodel'], null=False)),
            ('_tagulous_migrationtestmodel_tags', models.ForeignKey(orm[u'tagulous_tests_migration._tagulous_migrationtestmodel_tags'], null=False))
        ))
        db.create_unique(m2m_table_name, ['migrationtestmodel_id', '_tagulous_migrationtestmodel_tags_id'])


    def backwards(self, orm):
        # Removing unique constraint on '_Tagulous_MigrationTestModel_singletag', fields ['slug']
        db.delete_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_singletag', ['slug'])

        # Removing unique constraint on '_Tagulous_MigrationTestModel_tags', fields ['slug']
        db.delete_unique(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags', ['slug'])

        # Deleting model '_Tagulous_MigrationTestModel_tags'
        db.delete_table(u'tagulous_tests_migration__tagulous_migrationtestmodel_tags')

        # Deleting model '_Tagulous_MigrationTestModel_singletag'
        db.delete_table(u'tagulous_tests_migration__tagulous_migrationtestmodel_singletag')

        # Deleting field 'MigrationTestModel.singletag'
        db.delete_column(u'tagulous_tests_migration_migrationtestmodel', 'singletag_id')

        # Removing M2M table for field tags on 'MigrationTestModel'
        db.delete_table(db.shorten_name(u'tagulous_tests_migration_migrationtestmodel_tags'))


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
            'Meta': {'ordering': "('name',)", 'unique_together': "(('slug',),)", 'object_name': '_Tagulous_MigrationTestModel_tags', '_bases': ['tagulous.models.BaseTagModel']},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'protected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        u'tagulous_tests_migration.migrationtestmodel': {
            'Meta': {'object_name': 'MigrationTestModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'singletag': ('tagulous.models.fields.SingleTagField', [], {'_set_tag_meta': 'True', 'null': 'True', 'to': u"orm['tagulous_tests_migration._Tagulous_MigrationTestModel_singletag']", 'blank': 'True'}),
            'tags': ('tagulous.models.fields.TagField', [], {'to': u"orm['tagulous_tests_migration._Tagulous_MigrationTestModel_tags']", '_set_tag_meta': 'True'})
        }
    }

    complete_apps = ['tagulous_tests_migration']