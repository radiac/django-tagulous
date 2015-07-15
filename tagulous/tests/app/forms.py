from django import forms

import tagulous
from tagulous.tests.app import models


# Straight form fields

class SingleTagFieldForm(forms.Form):
    singletag = tagulous.forms.SingleTagField()
    
class TagFieldForm(forms.Form):
    tags = tagulous.forms.TagField()


# SingleTagField model forms

class SingleTagFieldModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldModel

class SingleTagFieldOptionalModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldOptionalModel
        
class SingleTagFieldRequiredModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldRequiredModel

class SingleTagFieldOptionsModelForm(forms.ModelForm):
    class Meta:
        model = models.SingleTagFieldOptionsModel


# TagField model forms

class TagFieldModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldModel

class TagFieldOptionalModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldOptionalModel
        
class TagFieldRequiredModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldRequiredModel

class TagFieldOptionsModelForm(forms.ModelForm):
    class Meta:
        model = models.TagFieldOptionsModel
        

# Mixed model forms

class MixedNonTagRefModelForm(forms.ModelForm):
    class Meta:
        model = models.MixedNonTagRefTest
