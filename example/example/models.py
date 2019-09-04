"""
Models for example Tagulous app

Based on the usage examples in the documentation:
    http://radiac.net/projects/django-tagulous/documentation/usage/
"""
from __future__ import unicode_literals

from django.db import models
from django.utils import six

import tagulous.models


class Skill(tagulous.models.TagTreeModel):
    class TagMeta:
        initial = [
            'Python/Django',
            'Python/Flask',
            'JavaScript/JQuery',
            'JavaScript/Angular.js',
            'Linux/nginx',
            'Linux/uwsgi',
        ]
        space_delimiter = False
        autocomplete_view = 'person_skills_autocomplete'


class Person(models.Model):
    name = models.CharField(max_length=255)
    title = tagulous.models.SingleTagField(
        initial="Mr, Mrs", help_text=(
            "This is a SingleTagField - effectively a CharField with "
            "dynamic choices"
        ),
        on_delete=models.CASCADE,
    )
    skills = tagulous.models.TagField(
        Skill, help_text="This field does not split on spaces",
    )
    hobbies = tagulous.models.TagField(
        initial="eating, coding, gaming",
        force_lowercase=True,
        blank=True,
        help_text="This field splits on spaces and commas",
    )
    class Meta:
        verbose_name_plural = 'people'
