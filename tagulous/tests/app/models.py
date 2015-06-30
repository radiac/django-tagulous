"""
Test models
"""

from django.db import models

import tagulous


###############################################################################
####### Models for testing SingleTagField
###############################################################################

class SingleTagFieldModel(models.Model):
    """
    For testing simple single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    title = tagulous.models.SingleTagField(blank=True, null=True)

class SingleTagFieldOptionalModel(models.Model):
    """
    Test optional single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.SingleTagField(blank=True, null=True)
    
class SingleTagFieldRequiredModel(models.Model):
    """
    Test required single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.SingleTagField(blank=False, null=False)


class SingleTagFieldMultipleModel(models.Model):
    """
    For testing multiple single tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag1 = tagulous.models.SingleTagField(blank=False, null=False)
    tag2 = tagulous.models.SingleTagField(blank=False, null=False)
    tag3 = tagulous.models.SingleTagField(blank=False, null=False)


class SingleTagFieldOptionsModel(models.Model):
    """
    For testing model and form SingleTagField options
    """
    name = models.CharField(blank=True, max_length=100)
    initial_string = tagulous.models.SingleTagField(
        blank=True, null=True, initial='Mr, Mrs, Ms',
    )
    initial_list = tagulous.models.SingleTagField(
        blank=True, null=True, initial=['Mr', 'Mrs', 'Ms'],
    )
    protect_initial_true = tagulous.models.SingleTagField(
        blank=True, null=True, protect_initial=True, initial='Mr',
    )
    protect_initial_false = tagulous.models.SingleTagField(
        blank=True, null=True, protect_initial=False, initial='Mr',
    )
    protect_all_true = tagulous.models.SingleTagField(
        blank=True, null=True, protect_all=True,
    )
    protect_all_false = tagulous.models.SingleTagField(
        blank=True, null=True, protect_all=False,
    )
    case_sensitive_true = tagulous.models.SingleTagField(
        blank=True, null=True, case_sensitive=True, initial='Mr',
    )
    case_sensitive_false = tagulous.models.SingleTagField(
        blank=True, null=True, case_sensitive=False, initial='Mr',
    )
    force_lowercase_true = tagulous.models.SingleTagField(
        blank=True, null=True, force_lowercase=True,
    )
    force_lowercase_false = tagulous.models.SingleTagField(
        blank=True, null=True, force_lowercase=False,
    )
    # max_count doesn't apply to SingleTagField
    autocomplete_view = tagulous.models.SingleTagField(
        blank=True, null=True,
        autocomplete_view='tagulous_tests_app-SingleTagFieldOptionsModel',
    )
    autocomplete_limit = tagulous.models.SingleTagField(
        blank=True, null=True, autocomplete_limit=3
    )
    autocomplete_settings = tagulous.models.SingleTagField(
        blank=True, null=True, autocomplete_settings={
            'setting1': 1,
            'setting2': True,
            'setting3': 'example',
        }
    )



###############################################################################
####### Models for testing TagField
###############################################################################

class TagFieldModel(models.Model):
    """
    For testing basic tags
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField()


class TagFieldMultipleModel(models.Model):
    """
    For testing multiple tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tags1 = tagulous.models.TagField(blank=False, null=False)
    tags2 = tagulous.models.TagField(blank=False, null=False)
    tags3 = tagulous.models.TagField(blank=False, null=False)


class TagFieldOptionsModel(models.Model):
    """
    For testing model and form TagField options
    """
    name = models.CharField(blank=True, max_length=100)
    initial_string = tagulous.models.TagField(
        blank=True, null=True, initial='Adam, Brian, Chris',
    )
    initial_list = tagulous.models.TagField(
        blank=True, null=True, initial=['Adam', 'Brian', 'Chris'],
    )
    protect_initial_true = tagulous.models.TagField(
        blank=True, null=True, protect_initial=True, initial='Adam',
    )
    protect_initial_false = tagulous.models.TagField(
        blank=True, null=True, protect_initial=False, initial='Adam',
    )
    protect_all_true = tagulous.models.TagField(
        blank=True, null=True, protect_all=True,
    )
    protect_all_false = tagulous.models.TagField(
        blank=True, null=True, protect_all=False,
    )
    case_sensitive_true = tagulous.models.TagField(
        blank=True, null=True, case_sensitive=True, initial='Adam',
    )
    case_sensitive_false = tagulous.models.TagField(
        blank=True, null=True, case_sensitive=False, initial='Adam',
    )
    force_lowercase_true = tagulous.models.TagField(
        blank=True, null=True, force_lowercase=True,
    )
    force_lowercase_false = tagulous.models.TagField(
        blank=True, null=True, force_lowercase=False,
    )
    case_sensitive_true_force_lowercase_true = tagulous.models.TagField(
        blank=True, null=True, case_sensitive=False, force_lowercase=True,
    )
    max_count = tagulous.models.TagField(
        blank=True, null=True, max_count=3,
    )
    autocomplete_view = tagulous.models.TagField(
        blank=True, null=True,
        autocomplete_view='tagulous_tests_app-TagFieldOptionsModel',
    )
    autocomplete_limit = tagulous.models.TagField(
        blank=True, null=True, autocomplete_limit=3
    )
    autocomplete_settings = tagulous.models.TagField(
        blank=True, null=True, autocomplete_settings={
            'setting1': 1,
            'setting2': True,
            'setting3': 'example',
        }
    )


###############################################################################
####### Models for testing a mix of fields
###############################################################################

class MixedTestTagModel(tagulous.models.TagModel):
    pass

class MixedTest(models.Model):
    """
    For testing merging of tags
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(
        MixedTestTagModel, related_name='mixed_singletag',
        blank=True,
    )
    tags = tagulous.models.TagField(
        MixedTestTagModel, related_name='mixed_tags',
        blank=True,
    )

class MixedRefTest(models.Model):
    """
    Multiple models referencing tag tables
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(
        MixedTest.singletag.tag_model, related_name='mixed_ref_singletag',
        blank=True,
    )
    tags = tagulous.models.TagField(
        MixedTest.tags.tag_model, related_name='mixed_ref_tags',
        blank=True,
    )
    
class NonTagRefTest(models.Model):
    """
    ForeignKeys and ManyToManyFields directly referencing a tag model
    """
    name = models.CharField(max_length=10)
    fk = models.ForeignKey(
        MixedTest.singletag.tag_model, related_name='non_tag_fk',
        blank=True,
    )
    mm = models.ManyToManyField(
        MixedTest.tags.tag_model, related_name='non_tag_mm',
        blank=True,
    )


class MixedNonTagModel(tagulous.models.TagModel):
    pass
class MixedNonTagRefTest(models.Model):
    """
    Tag fields and conventional relationships referencing a tag model
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(MixedNonTagModel, blank=True, related_name='singletags')
    tags = tagulous.models.TagField(MixedNonTagModel, blank=True, related_name='tags')
    fk = models.ForeignKey(MixedNonTagModel, blank=True, null=True, related_name='fk')
    mm = models.ManyToManyField(MixedNonTagModel, blank=True, related_name='mm')


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


class TreeTest(models.Model):
    """
    For testing tag trees
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(tree=True, blank=True)
    tags = tagulous.models.TagField(tree=True, blank=True)
