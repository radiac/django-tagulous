from __future__ import unicode_literals

from django import forms
from django.utils import six

import tagulous
from tests.tagulous_tests_app import models


# Straight form fields

class SingleTagFieldForm(forms.Form):
    singletag = tagulous.forms.SingleTagField()
    
class TagFieldForm(forms.Form):
    tags = tagulous.forms.TagField()


# SingleTagField model forms

class SingleTagFieldModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldModel
        exclude = ()

class SingleTagFieldOptionalModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldOptionalModel
        exclude = ()
        
class SingleTagFieldRequiredModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldRequiredModel
        exclude = ()

class SingleTagFieldOptionsModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldOptionsModel
        exclude = ()


# TagField model forms

class TagFieldModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldModel
        exclude = ()

class TagFieldOptionalModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldOptionalModel
        exclude = ()
        
class TagFieldRequiredModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldRequiredModel
        exclude = ()

class TagFieldOptionsModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldOptionsModel
        exclude = ()
        

# Mixed model forms

class MixedNonTagRefModelForm(forms.ModelForm):
    class Meta:
        model = models.MixedNonTagRefTest
        exclude = ()


# Formsets

SimpleMixedSingleInline = forms.models.inlineformset_factory(
    models.SimpleMixedTest.singletag.tag_model,
    models.SimpleMixedTest,
    formset=tagulous.forms.TaggedInlineFormSet,
    fields=('name',),
)

