"""
Forms for example Tagulous app
"""
from django import forms

from example import models


class PersonForm(forms.ModelForm):
    class Meta:
        fields = ["name", "title", "skills", "hobbies"]
        model = models.Person
