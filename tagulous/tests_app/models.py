"""
Test models
"""

from django.db import models

from tagulous import SingleTagField, TagField, TagModel


#
# Models for testing TagField
#

class TestModel(models.Model):
    """
    For testing basic tags
    """
    name = models.CharField(blank=True, max_length=100)
    tags = TagField()

class OrderTestModel(models.Model):
    """
    For testing ordering of a TagField when next to other M2M fields
    """
    first   = models.ManyToManyField(TestModel, related_name="order_first_set")
    tags    = TagField()
    second  = models.ManyToManyField(TestModel, related_name="order_second_set")
    
class MultiTestModel(models.Model):
    """
    For testing multiple tag fields, tag options
    """
    name = models.CharField(blank=True, max_length=100)
    tagset1 = TagField(protect_all=True, case_sensitive=True)
    tagset2 = TagField(initial="blue, green, red", force_lowercase=True)
    tagset3 = TagField(initial='Adam', protect_initial=False)
    
class CustomTestTagModel(TagModel):
    class TagMeta:
        protect_all = True
        initial     = 'django, javascript'

class CustomTestFirstModel(models.Model):
    """
    For testing a custom test model
    """
    name = models.CharField(blank=True, max_length=100)
    tags = TagField(CustomTestTagModel)

class CustomTestSecondModel(models.Model):
    """
    For testing a custom test model shared between two models
    """
    name = models.CharField(blank=True, max_length=100)
    tags = TagField(CustomTestTagModel)


#
# Models for testing SingleTagField
#

class SingleTestModel(models.Model):
    name = models.CharField(blank=True, max_length=100)
    title = SingleTagField(blank=True, null=True)

class SingleOrderTestModel(models.Model):
    """
    For testing ordering of a SingleTagField when next to other non-M2M fields
    """
    first   = models.CharField(blank=True, max_length=100)
    second  = models.ForeignKey(SingleTestModel)
    third   = models.CharField(blank=True, max_length=100)
    tag     = SingleTagField() # blank=False, null=False
    fourth  = models.CharField(blank=True, max_length=100)
    fifth   = models.CharField(blank=True, max_length=100)
    
class SingleRequiredTestModel(models.Model):
    name = models.CharField(blank=True, max_length=100)
    tag = SingleTagField(blank=False, null=False)
    
class SingleOptionalTestModel(models.Model):
    name = models.CharField(blank=True, max_length=100)
    tag = SingleTagField(blank=True, null=True)
