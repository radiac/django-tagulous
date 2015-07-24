# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MigrationTestModel'
        db.create_table(u'tagulous_tests_migration_migrationtestmodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'tagulous_tests_migration', ['MigrationTestModel'])


    def backwards(self, orm):
        # Deleting model 'MigrationTestModel'
        db.delete_table(u'tagulous_tests_migration_migrationtestmodel')


    models = {
        u'tagulous_tests_migration.migrationtestmodel': {
            'Meta': {'object_name': 'MigrationTestModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['tagulous_tests_migration']