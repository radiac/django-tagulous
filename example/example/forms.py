"""
Forms for example Tagulous app
"""
from __future__ import unicode_literals

from django import forms
from django.utils import six

from example import models


class PersonForm(forms.ModelForm):
    class Meta:
        fields = ['name', 'title', 'skills', 'hobbies']
        model = models.Person
