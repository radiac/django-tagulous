from django import forms

from tagulous.tests.app import models

class SingleTagFieldForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldModel

class SingleTagFieldOptionsForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldOptionsModel


class TagFieldForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldModel

class TagFieldOptionsForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldOptionsModel
