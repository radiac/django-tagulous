# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tagulous.models.fields
import tagulous.models.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='_Tagulous_Person_hobbies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField()),
                ('count', models.IntegerField(default=0, help_text='Internal counter of how many times this tag is in use')),
                ('protected', models.BooleanField(default=False, help_text='Will not be deleted when the count reaches 0')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(tagulous.models.models.BaseTagModel, models.Model),
        ),
        migrations.CreateModel(
            name='_Tagulous_Person_title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField()),
                ('count', models.IntegerField(default=0, help_text='Internal counter of how many times this tag is in use')),
                ('protected', models.BooleanField(default=False, help_text='Will not be deleted when the count reaches 0')),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(tagulous.models.models.BaseTagModel, models.Model),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('hobbies', tagulous.models.fields.TagField(force_lowercase=True, initial='eating, coding, gaming', to='example._Tagulous_Person_hobbies', blank=True, help_text='This field splits on spaces and commas', _set_tag_meta=True)),
            ],
            options={
                'verbose_name_plural': 'people',
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField()),
                ('count', models.IntegerField(default=0, help_text='Internal counter of how many times this tag is in use')),
                ('protected', models.BooleanField(default=False, help_text='Will not be deleted when the count reaches 0')),
                ('path', models.TextField()),
                ('label', models.CharField(help_text='The name of the tag, without ancestors', max_length=255)),
                ('level', models.IntegerField(default=1, help_text='The level of the tag in the tree')),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='example.Skill', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
                'abstract': False,
            },
            bases=(tagulous.models.models.BaseTagTreeModel, models.Model),
        ),
        migrations.AddField(
            model_name='person',
            name='skills',
            field=tagulous.models.fields.TagField(to='example.Skill', autocomplete_view='person_skills_autocomplete', space_delimiter=False, help_text='This field does not split on spaces', _set_tag_meta=True, initial='JavaScript/Angular.js, JavaScript/JQuery, Linux/nginx, Linux/uwsgi, Python/Django, Python/Flask', tree=True),
        ),
        migrations.AddField(
            model_name='person',
            name='title',
            field=tagulous.models.fields.SingleTagField(initial='eating, coding, gaming', force_lowercase=True, blank=True, to='example._Tagulous_Person_title', help_text='This is a SingleTagField - effectively a CharField with dynamic choices', _set_tag_meta=True, null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='_tagulous_person_title',
            unique_together=set([('slug',)]),
        ),
        migrations.AlterUniqueTogether(
            name='_tagulous_person_hobbies',
            unique_together=set([('slug',)]),
        ),
        migrations.AlterUniqueTogether(
            name='skill',
            unique_together=set([('slug', 'parent')]),
        ),
    ]
