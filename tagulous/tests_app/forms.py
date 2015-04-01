from django import forms

from tagulous.tests_app import models


class FormTest(forms.ModelForm):
    class Meta:
        model = models.FormTest

class SingleFormTest(forms.ModelForm):
    class Meta:
        model = models.SingleFormTest
