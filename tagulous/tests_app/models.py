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

class SingleOptionalTestModel(models.Model):
    """
    Test optional single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.SingleTagField(blank=True, null=True)
    
class SingleRequiredTestModel(models.Model):
    """
    Test required single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.SingleTagField(blank=False, null=False)



#
# Models for testing TagField
#

class TagModel(models.Model):
    """
    For testing basic tags
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField()




#
# Models for testing a mix of fields
#

class MixedTestTagModel(tagulous.models.TagModel):
    pass

class MixedTest(models.Model):
    """
    For testing merging of tags
    """
    name = models.CharField(max_length=10)
    singletags = tagulous.models.SingleTagField(
        MixedTestTagModel, related_name='as',
        blank=True,
    )
    tags = tagulous.models.TagField(
        MixedTestTagModel, related_name='at',
        blank=True,
    )

class MixedRefTest(models.Model):
    name = models.CharField(max_length=10)
    singletags = tagulous.models.SingleTagField(
        MixedTest.singletags.tag_model, related_name='bs',
        blank=True,
    )
    tags = tagulous.models.TagField(
        MixedTest.tags.tag_model, related_name='bt',
        blank=True,
    )


class MixedOrderTest(models.Model):
    """
    For testing ordering of a SingleTagField and TagField when next to other
    M2M and non-M2M fields
    """
    char1   = models.CharField(blank=True, max_length=10)
    fk1     = models.ForeignKey(MixedTest, related_name="order_fk1")
    char2   = models.CharField(blank=True, max_length=10)
    single1 = tagulous.models.SingleTagField()
    char3   = models.CharField(blank=True, max_length=10)
    m2m1    = models.ManyToManyField(MixedTest, related_name="order_m2m1")
    char4   = models.CharField(blank=True, max_length=10)
    multi1  = tagulous.models.TagField()
    char5   = models.CharField(blank=True, max_length=10)
    m2m2    = models.ManyToManyField(MixedTest, related_name="order_m2m2")
    char6   = models.CharField(blank=True, max_length=10)
    fk2     = models.ForeignKey(MixedTest, related_name="order_fk2")
    char7   = models.CharField(blank=True, max_length=10)


#
# OLD TESTS
#



#
# Models for testing TagField
#

class TestModel(models.Model):
    """
    For testing basic tags
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField()


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
