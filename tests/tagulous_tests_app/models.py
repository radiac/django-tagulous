"""
Test models
"""
from __future__ import unicode_literals

from django.db import models
from django.utils import six

import tagulous


###############################################################################
####### Models for testing TagModel
###############################################################################

class TagMetaAbstractModel(tagulous.models.TagModel):
    """
    An abstract tag model with TagMeta definition
    """
    class Meta:
        abstract = True
    class TagMeta:
        initial = 'Adam, Brian, Chris'
        force_lowercase = True
        max_count = 5

class TagMetaModel(TagMetaAbstractModel):
    """
    A tag model which inherits from TagMetaAbstractModel, with new and changed
    TagMeta values
    """
    class TagMeta:
        max_count = 10
        case_sensitive = True

class TagMetaUser(models.Model):
    """
    A tagged model which uses the TagMetaModel
    """
    name = models.CharField(blank=True, max_length=100)
    two = tagulous.models.TagField(TagMetaModel, blank=True, null=True)
    
    
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
        autocomplete_initial=True,
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
        autocomplete_view='tagulous_tests_app-null',
    )
    autocomplete_limit = tagulous.models.SingleTagField(
        blank=True, null=True,
        autocomplete_limit=3,
        # Limit only takes effect when there's a view
        autocomplete_view='tagulous_tests_app-null',
    )
    autocomplete_settings = tagulous.models.SingleTagField(
        blank=True, null=True, autocomplete_settings={
            'setting1': 1,
            'setting2': True,
            'setting3': 'example',
        }
    )
    class Meta:
        # Must set a short verbose name - tagulous auto-generated model
        # verbose names will be too long otherwise
        verbose_name = 'STFOM'


###############################################################################
####### Models for testing TagField
###############################################################################

class TagFieldModel(models.Model):
    """
    For testing basic tags
    """
    name = models.CharField(blank=True, max_length=100)
    tags = tagulous.models.TagField()

class TagFieldOptionalModel(models.Model):
    """
    Test optional tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.TagField(blank=True, null=True)
    
class TagFieldRequiredModel(models.Model):
    """
    Test required tag fields
    """
    name = models.CharField(blank=True, max_length=100)
    tag = tagulous.models.TagField(blank=False, null=False)

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
        autocomplete_initial=True,
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
        verbose_name_singular='case sensitive test'
    )
    max_count = tagulous.models.TagField(
        blank=True, null=True, max_count=3,
    )
    autocomplete_view = tagulous.models.TagField(
        blank=True, null=True,
        autocomplete_view='tagulous_tests_app-unlimited',
    )
    autocomplete_limit = tagulous.models.TagField(
        blank=True, null=True,
        autocomplete_limit=3,
        # Limit only takes effect when there's a view
        autocomplete_view='tagulous_tests_app-limited',
    )
    autocomplete_settings = tagulous.models.TagField(
        blank=True, null=True, autocomplete_settings={
            'setting1': 1,
            'setting2': True,
            'setting3': 'example',
        }
    )
    class Meta:
        # Set a short verbose name for tagulous auto-generated verbose name
        verbose_name = 'TFOM'


###############################################################################
####### Models for testing a mix of fields
###############################################################################

class SimpleMixedTest(models.Model):
    """
    For tests which need a SingleTagField and TagField
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(blank=True)
    tags = tagulous.models.TagField(blank=True)

class MixedTestTagModel(tagulous.models.TagModel):
    class TagMeta:
        get_absolute_url = lambda self: 'url for %s' % self

class MixedTest(models.Model):
    """
    For tests where it's useful for the SingleTagField and TagField to share
    a tag model
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
        blank=True, on_delete=models.CASCADE,
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
    fk = models.ForeignKey(MixedNonTagModel, blank=True, null=True, related_name='fk', on_delete=models.CASCADE)
    mm = models.ManyToManyField(MixedNonTagModel, blank=True, related_name='mm')


class MixedOrderTest(models.Model):
    """
    For testing ordering of a SingleTagField and TagField when next to other
    M2M and non-M2M fields
    """
    char1   = models.CharField(blank=True, max_length=10)
    fk1     = models.ForeignKey(MixedTest, related_name="order_fk1", on_delete=models.CASCADE)
    char2   = models.CharField(blank=True, max_length=10)
    single1 = tagulous.models.SingleTagField()
    char3   = models.CharField(blank=True, max_length=10)
    m2m1    = models.ManyToManyField(MixedTest, related_name="order_m2m1")
    char4   = models.CharField(blank=True, max_length=10)
    multi1  = tagulous.models.TagField()
    char5   = models.CharField(blank=True, max_length=10)
    m2m2    = models.ManyToManyField(MixedTest, related_name="order_m2m2")
    char6   = models.CharField(blank=True, max_length=10)
    fk2     = models.ForeignKey(MixedTest, related_name="order_fk2", on_delete=models.CASCADE)
    char7   = models.CharField(blank=True, max_length=10)


class MixedStringTagModel(tagulous.models.TagModel):
    pass
class MixedStringTo(models.Model):
    """
    A tagged model with fields which refers to a tag model by string, rather
    than by class
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(
        'MixedStringTagModel', related_name='tag_meta_string_singletag',
        blank=True,
    )
    tags = tagulous.models.TagField(
        'MixedStringTagModel', related_name='tag_meta_string_tags',
        blank=True,
    )

class MixedSelfTo(tagulous.models.TagModel):
    """
    A tagged tag model, with tag fields which refers itself using 'self'
    """
    alternate = tagulous.models.SingleTagField('self', blank=True)
    related = tagulous.models.TagField('self', blank=True)
    class TagMeta:
        force_lowercase = True



class TreeTest(models.Model):
    """
    For testing tag trees
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(tree=True, blank=True)
    tags = tagulous.models.TagField(tree=True, blank=True)

class CustomTagTree(tagulous.models.TagTreeModel):
    """
    Custom tag tree model
    """
    pass

class CustomTreeTest(models.Model):
    """
    For testing custom tag trees
    """
    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(
        'CustomTagTree', blank=True, related_name='custom_singletag',
    )
    tags = tagulous.models.TagField(
        'CustomTagTree', blank=True, related_name='custom_tags',
    )
