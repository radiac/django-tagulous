# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tagulous.models.fields
import tagulous.models.migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tagulous_tests_migration', '0002_tagged'),
    ]

    operations = [
        migrations.AddField(
            model_name='_tagulous_migrationtestmodel_tags',
            name='parent',
            field=models.ForeignKey(to='tagulous_tests_migration._Tagulous_MigrationTestModel_tags', related_name='children', blank=True, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='_tagulous_migrationtestmodel_tags',
            name='label',
            field=models.CharField(default='-', max_length=255, help_text=b'The name of the tag, without ancestors'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='_tagulous_migrationtestmodel_tags',
            name='level',
            field=models.IntegerField(default=1, help_text=b'The level of the tag in the tree'),
            preserve_default=True,
        ),
    ] + tagulous.models.migrations.add_unique_field(
        model_name='_tagulous_migrationtestmodel_tags',
        name='path',
        field=models.TextField(unique=True),
        preserve_default=False,
        set_fn=lambda obj: setattr(obj, 'path', str(obj.pk)),
    ) + [
        migrations.AlterField(
            model_name='migrationtestmodel',
            name='tags',
            field=tagulous.models.fields.TagField(to='tagulous_tests_migration._Tagulous_MigrationTestModel_tags', help_text=b'Enter a comma-separated tag string', _set_tag_meta=True, tree=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='_tagulous_migrationtestmodel_tags',
            unique_together=set([('slug', 'parent')]),
        ),
        tagulous.models.migrations.ChangeModelBases(
            name='_tagulous_migrationtestmodel_tags',
            bases=(tagulous.models.models.BaseTagTreeModel, models.Model),
        )
    ]
