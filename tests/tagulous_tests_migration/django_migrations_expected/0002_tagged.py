# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils import six

import tagulous.models.fields
import tagulous.models.models


class Migration(migrations.Migration):

    dependencies = [
        ('tagulous_tests_migration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='_Tagulous_MigrationTestModel_singletag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField()),
                ('count', models.IntegerField(default=0, help_text=b'Internal counter of how many times this tag is in use')),
                ('protected', models.BooleanField(default=False, help_text=b'Will not be deleted when the count reaches 0')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(tagulous.models.models.BaseTagModel, models.Model),
        ),
        migrations.CreateModel(
            name='_Tagulous_MigrationTestModel_tags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField()),
                ('count', models.IntegerField(default=0, help_text=b'Internal counter of how many times this tag is in use')),
                ('protected', models.BooleanField(default=False, help_text=b'Will not be deleted when the count reaches 0')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(tagulous.models.models.BaseTagModel, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name='_tagulous_migrationtestmodel_tags',
            unique_together=set([('slug',)]),
        ),
        migrations.AlterUniqueTogether(
            name='_tagulous_migrationtestmodel_singletag',
            unique_together=set([('slug',)]),
        ),
        migrations.AddField(
            model_name='migrationtestmodel',
            name='singletag',
            field=tagulous.models.fields.SingleTagField(force_lowercase=False, to='tagulous_tests_migration._Tagulous_MigrationTestModel_singletag', blank=True, help_text=b'Enter a comma-separated tag string', null=True, autocomplete_initial=True, autocomplete_view=b'tagulous_tests_app-null', autocomplete_limit=3, initial='Mr', protect_all=False, case_sensitive=True, protect_initial=True, _set_tag_meta=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='migrationtestmodel',
            name='tags',
            field=tagulous.models.fields.TagField(force_lowercase=True, to='tagulous_tests_migration._Tagulous_MigrationTestModel_tags', protect_initial=True, help_text=b'Enter a comma-separated tag string', case_sensitive=True, autocomplete_initial=True, autocomplete_view=b'tagulous_tests_app-null', autocomplete_limit=3, initial='Mr', protect_all=False, _set_tag_meta=True),
            preserve_default=True,
        ),
    ]
