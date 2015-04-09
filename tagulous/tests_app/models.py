"""
Test models
"""

from django.db import models

import tagulous


#
# Models for testing SingleTagField
#

class SingleTestModel(models.Model):
    """
    For testing simple single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    title = tagulous.models.SingleTagField(blank=True, null=True)

class SingleOrderTestModel(models.Model):
    """
    For testing ordering of a SingleTagField when next to other non-M2M fields
    """
    first   = models.CharField(blank=True, max_length=100)
    second  = models.ForeignKey(SingleTestModel)
    third   = models.CharField(blank=True, max_length=100)
    tag     = tagulous.models.SingleTagField() # blank=False, null=False
    fourth  = models.CharField(blank=True, max_length=100)
    fifth   = models.CharField(blank=True, max_length=100)
    
class SingleRequiredTestModel(models.Model):
    """
    Test required single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.SingleTagField(blank=False, null=False)
    
class SingleOptionalTestModel(models.Model):
    """
    Test optional single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.SingleTagField(blank=True, null=True)


#
# Models for testing TagField
#

class TestModel(models.Model):
    """
    For testing basic tags
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField()

class OrderTestModel(models.Model):
    """
    For testing ordering of a TagField when next to other M2M fields
    """
    first   = models.ManyToManyField(TestModel, related_name="order_first_set")
    tags    = tagulous.models.TagField()
    second  = models.ManyToManyField(TestModel, related_name="order_second_set")
    
class MultiTestModel(models.Model):
    """
    For testing multiple tag fields, tag options
    """
    name = models.CharField(blank=True, max_length=100)
    tagset1 = tagulous.models.TagField(protect_all=True, case_sensitive=True)
    tagset2 = tagulous.models.TagField(initial="blue, green, red", force_lowercase=True)
    tagset3 = tagulous.models.TagField(initial='Adam', protect_initial=False)
    
class CustomTestTagModel(tagulous.models.TagModel):
    class TagMeta:
        protect_all = True
        initial     = 'django, javascript'

class CustomTestFirstModel(models.Model):
    """
    For testing a custom test model
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField(CustomTestTagModel)

class CustomTestSecondModel(models.Model):
    """
    For testing a custom test model shared between two models
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField(CustomTestTagModel)



#
# Models for testing merging
#

class MergeTestTagModel(tagulous.models.TagModel):
    pass

class MergeTest(models.Model):
    """
    For testing merging of tags
    """
    name = models.CharField(max_length=10)
    singletags = tagulous.models.SingleTagField(
        MergeTestTagModel, related_name='as',
        blank=True,
    )
    tags = tagulous.models.TagField(
        MergeTestTagModel, related_name='at',
        blank=True,
    )

class MergeRefTest(models.Model):
    name = models.CharField(max_length=10)
    singletags = tagulous.models.SingleTagField(
        MergeTest.singletags.model, related_name='bs',
        blank=True,
    )
    tags = tagulous.models.TagField(
        MergeTest.tags.model, related_name='bt',
        blank=True,
    )


#
# Models for testing forms
#

class FormTest(models.Model):
    """
    For testing multiple tag fields in model forms
    """
    tagset1 = tagulous.models.TagField(initial="Adam, Brian, Chris", case_sensitive=True)
    tagset2 = tagulous.models.TagField(initial="blue, green, red", force_lowercase=True)
    tagset3 = tagulous.models.TagField(initial='html, django')

class SingleFormTest(models.Model):
    """
    For testing single tag fields in model forms
    """
    tag1 = tagulous.models.SingleTagField(initial="Adam, Brian, Chris", case_sensitive=True)
    tag2 = tagulous.models.SingleTagField(initial="blue, green, red", force_lowercase=True)
    tag3 = tagulous.models.SingleTagField(initial='html, django')
