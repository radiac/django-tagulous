import unittest

from django.db import models
from django.core import exceptions
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

from tagulous import constants as tag_constants
from tagulous import models as tag_models
from tagulous import forms as tag_forms
from tagulous import utils as tag_utils
from tagulous import settings as tag_settings

from tagulous.tests_app.models import \
    TestModel, MultiTestModel, CustomTestTagModel, \
    CustomTestFirstModel, CustomTestSecondModel

from tagulous.tests_app import models as test_models
from tagulous.tests_app import forms as test_forms


class TagTestManager(object):
    """
    Test mixin to help test tag models
    """
    manage_models = None
    
    def setUp(self):
        """
        Ensure initial data is in the tag models
        """
        if self.manage_models is not None:
            for model in self.manage_models:
                tag_models.initial.model_initialise_tags(model)
                tag_models.initial.model_initialise_tags(model)
        
        if hasattr(self, 'setUpExtra'):
            self.setUpExtra()
        
    def create(self, model, **kwargs):
        ##30# ++ This can be replaced when we've got create() working properly
        pre = {}
        post = {}
        for field_name, val in kwargs.items():
            if isinstance(
                model._meta.get_field(field_name),
                (tag_models.SingleTagField, tag_models.TagField),
            ):
                post[field_name] = val
            else:
                pre[field_name] = val
        
        item = model.objects.create(**pre)
        for field_name, val in post.items():
            setattr(item, field_name, val)
        item.save()
        
        return item
    
    def assertInstanceEquals(self, instance, **kwargs):
        # First, reload instance
        instance = instance.__class__.objects.get(pk=instance.pk)
        
        # Check values
        for field_name, val in kwargs.items():
            try:
                if isinstance(
                    instance.__class__._meta.get_field(field_name),
                    (tag_models.SingleTagField, tag_models.TagField)
                ) and isinstance(val, basestring):
                    self.assertEqual(str(getattr(instance, field_name)), val)
                else:
                    self.assertEqual(getattr(instance, field_name), val)
            except AssertionError, e:
                self.fail(
                    'Instances not equal for field %s: %s' % (field_name, e)
                )

    def assertTagModel(self, model, tag_counts):
        """
        Assert the tag model matches the specified tag counts
        """
        if len(tag_counts) != model.objects.count():
            self.fail("Incorrect number of tags in '%s'; expected %d, got %d" % (model, len(tag_counts), model.objects.count()))
        
        for tag_name, count in tag_counts.items():
            try:
                tag = model.objects.get(name=tag_name)
            except model.DoesNotExist:
                self.fail("Tag model missing expected tag '%s'" % tag_name)
            if tag.count != count:
                self.fail("Tag count for '%s' incorrect; expected %d, got %d" % (tag_name, count, tag.count))
        
    def debugTagModel(self, field):
        print "-=-=-=-=-=-"
        print "Tag model: %s" % field.tag_model
        for tag in field.tag_model.objects.all():
            print '%s: %d' % (tag.name, tag.count)
        print "-=-=-=-=-=-"


###############################################################################
######################################################## Tag options
###############################################################################
####### tagulous.options
###############################################################################


class TagOptionsTest(TestCase):
    """
    Test TagOptions
    """
    def test_defaults(self):
        opt = tag_models.TagOptions()
        self.assertEqual(opt.items(with_defaults=False), {})
        self.assertEqual(opt.items(), tag_constants.OPTION_DEFAULTS)
        self.assertEqual(opt.field_items(with_defaults=False), {})
        self.assertEqual(opt.field_items(), dict([
            (k, v) for k, v in tag_constants.OPTION_DEFAULTS.items()
            if k in tag_constants.FIELD_OPTIONS
        ]))

    # ++ more


###############################################################################
######################################################## Utils
###############################################################################
####### tagulous.utils
###############################################################################

class UtilsTest(TestCase):
    """
    Test TagOptions
    """
    def test_parse_tags_commas(self):
        tags = tag_utils.parse_tags("adam,brian,chris")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
    
    def test_parse_tags_spaces(self):
        tags = tag_utils.parse_tags("adam brian chris")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        
    def test_parse_tags_commas_and_spaces(self):
        tags = tag_utils.parse_tags("adam, brian chris")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian chris")
        
    def test_parse_tags_commas_over_spaces(self):
        tags = tag_utils.parse_tags("adam brian  ,  chris")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam brian")
        self.assertEqual(tags[1], "chris")
        
    def test_parse_tags_order(self):
        tags = tag_utils.parse_tags("chris, adam, brian")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        
    def test_parse_tags_quotes(self):
        tags = tag_utils.parse_tags('"adam, one"')
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "adam, one")
        
    def test_parse_tags_quotes_comma_delim(self):
        tags = tag_utils.parse_tags('"adam, one","brian, two","chris, three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam, one")
        self.assertEqual(tags[1], "brian, two")
        self.assertEqual(tags[2], "chris, three")
        
    def test_parse_tags_quotes_space_delim(self):
        tags = tag_utils.parse_tags('"adam one" "brian two" "chris three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam one")
        self.assertEqual(tags[1], "brian two")
        self.assertEqual(tags[2], "chris three")
        
    def test_parse_tags_quotes_comma_delim_spaces_ignored(self):
        tags = tag_utils.parse_tags('"adam, one"  ,  "brian, two"  ,  "chris, three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam, one")
        self.assertEqual(tags[1], "brian, two")
        self.assertEqual(tags[2], "chris, three")
        
    def test_parse_tags_quotes_comma_delim_early_wins(self):
        tags = tag_utils.parse_tags('"adam one","brian two" "chris three"')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam one")
        self.assertEqual(tags[1], 'brian two" "chris three')
        
    def test_parse_tags_quotes_comma_delim_late_wins(self):
        tags = tag_utils.parse_tags('"adam one" "brian two","chris three"')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam one" "brian two')
        self.assertEqual(tags[1], "chris three")
        
    def test_parse_tags_quotes_dont_delimit(self):
        tags = tag_utils.parse_tags('adam"brian,chris dave')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam"brian')
        self.assertEqual(tags[1], "chris dave")
        
    def test_parse_tags_quotes_dont_close(self):
        tags = tag_utils.parse_tags('"adam,one","brian,two","chris, dave')
        self.assertEqual(len(tags), 3)
        # Will be sorted, " comes first
        self.assertEqual(tags[0], '"chris, dave')
        self.assertEqual(tags[1], "adam,one")
        self.assertEqual(tags[2], "brian,two")
    
    def test_parse_tags_quotes_and_unquoted(self):
        tags = tag_utils.parse_tags('adam , "brian, chris" , dave')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian, chris")
        self.assertEqual(tags[2], "dave")
    
    def test_parse_tags_quotes_order(self):
        tags = tag_utils.parse_tags('chris, "adam", brian')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        
    def test_parse_tags_quotes_escaped(self):
        """
        Tests quotes when delimiter is already comma
        """
        tags = tag_utils.parse_tags('adam, br""ian, ""chris, dave""')
        self.assertEqual(len(tags), 4)
        self.assertEqual(tags[0], '"chris')
        self.assertEqual(tags[1], 'adam')
        self.assertEqual(tags[2], 'br"ian')
        self.assertEqual(tags[3], 'dave"')
        
    def test_parse_tags_quotes_escaped_late(self):
        """
        Tests quotes when delimiter switches to comma
        """
        tags = tag_utils.parse_tags('""adam"" brian"", chris')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], '"adam" brian"')
        self.assertEqual(tags[1], 'chris')
        
    def test_parse_tags_empty_tag(self):
        tags = tag_utils.parse_tags('"adam" , , brian , ')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        
    def test_parse_tags_limit(self):
        with self.assertRaises(ValueError) as cm:
            print tag_utils.parse_tags("adam,brian,chris", 1)
        e = cm.exception
        self.assertEqual(str(e), 'This field can only have 1 argument')

    def test_parse_tags_limit_quotes(self):
        with self.assertRaises(ValueError) as cm:
            print tag_utils.parse_tags('"adam","brian",chris', 2)
        e = cm.exception
        self.assertEqual(str(e), 'This field can only have 2 arguments')

    def test_render_tags(self):
        tagstr = tag_utils.render_tags(['adam', 'brian', 'chris']);
        self.assertEqual(tagstr, 'adam, brian, chris')
    
    def test_render_tags_escapes_quotes(self):
        tagstr = tag_utils.render_tags(['ad"am', '"brian', 'chris"', '"dave"'])
        self.assertEqual(tagstr, '""brian, ""dave"", ad""am, chris""')
    
    def test_render_tags_quotes_commas_and_spaces(self):
        tagstr = tag_utils.render_tags(['adam brian', 'chris, dave', 'ed'])
        self.assertEqual(tagstr, '"adam brian", "chris, dave", ed')
    
    def test_parse_renders_tags(self):
        tagstr = 'adam, brian, chris'
        tags = tag_utils.parse_tags(tagstr)
        tagstr2 = tag_utils.render_tags(tags)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], 'adam')
        self.assertEqual(tags[1], 'brian')
        self.assertEqual(tags[2], 'chris')
        self.assertEqual(tagstr, tagstr2)
    
    def test_parse_renders_tags_complex(self):
        tagstr = '"""adam brian"", ""chris, dave", "ed, frank", gary'
        tags = tag_utils.parse_tags(tagstr)
        tagstr2 = tag_utils.render_tags(tags)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], '"adam brian", "chris, dave')
        self.assertEqual(tags[1], 'ed, frank')
        self.assertEqual(tags[2], 'gary')
        self.assertEqual(tagstr, tagstr2)
        

###############################################################################
######################################################## Tag models
###############################################################################
####### tagulous.models.models.BaseTagModel
####### tagulous.models.models.TagModel
###############################################################################

class TagModelTest(TagTestManager, TestCase):
    """
    Test tag models
    """
    manage_models = [
        test_models.MixedTest,
        test_models.MixedRefTest,
    ]
    
    @unittest.skip("buggy")
    def test_merge_tags(self):
        tag_model = test_models.MixedTestTagModel
        
        # Set up database
        a1 = self.create(test_models.MixedTest, name='a1', singletags='one', tags='one')
        a2 = self.create(test_models.MixedTest, name='a2', singletags='two', tags='two')
        a3 = self.create(test_models.MixedTest, name='a3', singletags='three', tags='three')

        b1 = self.create(test_models.MixedRefTest, name='b1', singletags='one', tags='one')
        b2 = self.create(test_models.MixedRefTest, name='b2', singletags='two', tags='two')
        b3 = self.create(test_models.MixedRefTest, name='b3', singletags='three', tags='three')
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'one': 4,
            'two': 4,
            'three': 4,
        })
        self.assertInstanceEquals(a1, singletags='one', tags='one')
        self.assertInstanceEquals(a2, singletags='two', tags='two')
        self.assertInstanceEquals(a3, singletags='three', tags='three')
        self.assertInstanceEquals(b1, singletags='one', tags='one')
        self.assertInstanceEquals(b2, singletags='two', tags='two')
        self.assertInstanceEquals(b3, singletags='three', tags='three')
        
        # Merge tags
        self.assertEqual(tag_model.objects.count(), 3)
        s1 = tag_model.objects.get(name='one')
        s1.merge_tags(
            tag_model.objects.filter(name__in=['one', 'two', 'three'])
        )
        
        # Check it's correct
        #self.assertTagModel(tag_model, {
        #    'one': 12,
        #})
        self.assertInstanceEquals(a1, singletags='one', tags='one')
        self.assertInstanceEquals(a2, singletags='one', tags='one')
        self.assertInstanceEquals(a3, singletags='one', tags='one')
        self.assertInstanceEquals(b1, singletags='one', tags='one')
        self.assertInstanceEquals(b2, singletags='one', tags='one')
        self.assertInstanceEquals(b3, singletags='one', tags='one')



###############################################################################
####################################################### Model single tag field
###############################################################################
####### tagulous.models.managers.BaseTagManager
####### tagulous.models.managers.SingleTagManager
####### tagulous.models.descriptors.BaseTagDescriptor
####### tagulous.models.descriptors.SingleTagDescriptor
####### tagulous.models.fields.SingleTagField
####### tagulous.models.fields.SingleTagField
###############################################################################

class ModelSingleTagFieldTest(TagTestManager, TestCase):
    """
    Test model SingleTagField
    """
    manage_models = [
        test_models.SingleTestModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.SingleTestModel.title.tag_model
        self.tag_field = test_models.SingleTestModel.title
    
    def test_descriptor(self):
        "Check SingleTagDescriptor is in place"
        self.assertTrue(isinstance(
            self.tag_field, tag_models.SingleTagDescriptor
        ))
    
    def test_tag_table(self):
        "Check the tag table exists"
        self.assertTrue(issubclass(
            self.tag_model, tag_models.TagModel
        ))
        
    def test_empty_value(self):
        "Check the descriptor returns None for no value"
        t1 = self.create(test_models.SingleTestModel, name="Test")
        self.assertInstanceEquals(t1, name="Test", title=None)
        self.assertTagModel(self.tag_model, {})
    
    def test_tag_assignment(self):
        "Check a tag string can be assigned to descriptor and returned"
        t1 = self.create(test_models.SingleTestModel, name="Test")
        t1.title = 'Mr'
        
        # Returned before save
        self.assertEqual(t1.title.__class__, self.tag_model)
        self.assertEqual(t1.title.name, 'Mr')
        self.assertEqual('%s' % t1.title, 'Mr')
        self.assertEqual(u'%s' % t1.title, 'Mr')
        self.assertTagModel(self.tag_model, {})
        
        # Returned after save
        t1.save()
        self.assertEqual(t1.title.__class__, self.tag_model)
        self.assertEqual(t1.title.name, 'Mr')
        self.assertEqual('%s' % t1.title, 'Mr')
        self.assertEqual(u'%s' % t1.title, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_tag_assignment_in_constructor(self):
        "Check a tag string can be passed in the constructor"
        t1 = test_models.SingleTestModel(name="Test", title='Mr')
        t1.save()
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_tag_assignment_in_object_create(self):
        "Check a tag string can be passed in object.create"
        t1 = test_models.SingleTestModel.objects.create(name='Test', title='Mr')
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_assign_by_object(self):
        """
        Check a tag object can be assigned to a SingleTagfield, and that its
        tag count is incremented
        """
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel(name='Test 2')
        t2.title = t1.title
        t2.save()
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t2.name, 'Test 2')
        self.assertEqual(str(t1.title), 'Mr')
        self.assertEqual(str(t2.title), 'Mr')
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
    
    def test_assign_by_object_in_constructor(self):
        "Check a tag object can be passed in the constructor"
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel(name='Test 2', title=t1.title)
        t2.save()
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
        
    def test_assign_by_object_in_object_create(self):
        "Check a tag object can be passed in object.create"
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel.objects.create(name='Test 2', title=t1.title)
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
    
    def test_change_decreases_count(self):
        "Check a tag string changes the count"
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel.objects.create(name='Test 2', title=t1.title)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
        t2.title = 'Mrs'
        t2.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        
    def test_delete_decreases_count(self):
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel.objects.create(name='Test 2', title=t1.title)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
        t2.delete()
        self.assertInstanceEquals(t1, name='Test 1', title='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_count_zero_deletes_tag(self):
        "Check a count of 0 deletes an unprotected tag"
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        t1.title = 'Mrs'
        t1.save()
        self.assertTagModel(self.tag_model, {
            'Mrs': 1,
        })
    
    def test_delete_decreases_correct(self):
        """
        Check that the actual tag in the database is decreased, not the one in
        the instance at time of deletion
        """
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel.objects.create(name='Test 2', title='Mrs')
        self.assertEqual(str(t1.title.name), 'Mr')
        self.assertEqual(str(t2.title.name), 'Mrs')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        
        # Now change the title and delete without saving
        t1.title = 'Mrs'
        self.assertEqual(str(t1.title.name), 'Mrs')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        t1.delete()
        
        # Check the original tag 'Mr' was decremented (and deleted)
        self.assertEqual(str(t1.title.name), 'Mrs')
        self.assertTagModel(self.tag_model, {
            'Mrs': 1,
        })
    
    def test_save_deleted_tag(self):
        "Check that a deleted tag in memory can be re-saved"
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        t1.delete()
        self.assertTagModel(self.tag_model, {})
        t1.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_multiple_unsaved(self):
        "Check that there's no leak between unsaved objects"
        t1 = test_models.SingleTestModel(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel(name='Test 1', title='Mrs')
        self.assertTagModel(self.tag_model, {})
        self.assertEqual(str(t1.title), 'Mr')
        self.assertEqual(str(t2.title), 'Mrs')
        t1.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        t2.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        self.assertEqual(str(t1.title), 'Mr')
        self.assertEqual(str(t2.title), 'Mrs')
    
    def test_load_instance(self):
        "Check that SingleTagField is loaded correctly"
        t1 = test_models.SingleTestModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTestModel.objects.get(pk=t1.pk)
        self.assertEqual(t1.title, t2.title)
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })


        


class ModelSingleTagFieldOptionalTest(TagTestManager, TestCase):
    """
    Test model SingleTagField
    """
    manage_models = [
        test_models.SingleOptionalTestModel,
    ]
    def test_optional_saves_without_exception(self):
        "Check an optional SingleTagField isn't required for save"
        try:
            t1 = test_models.SingleOptionalTestModel(name='Test 1')
            t1.save()
            t2 = test_models.SingleOptionalTestModel.objects.create(name='Test 1')
        except Exception, e:
            self.fail(
                'Optional SingleTagField raised exception unexpectedly: %s' % e
            )


class ModelSingleTagFieldRequiredTest(TagTestManager, TestCase):
    """
    Test model SingleTagField
    """
    manage_models = [
        test_models.SingleRequiredTestModel,
    ]
    def test_required_raises_exception_on_save(self):
        "Check a required SingleTagField raises an exception when saved"
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.SingleRequiredTestModel(name='Test')
            t1.save()
        self.assertEqual(cm.exception.messages[0], u'This field cannot be null.')
    
    def test_required_raises_exception_in_object_create(self):
        "Check a required SingleTagField raises an exception in object.create"
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.SingleRequiredTestModel.objects.create(name='Test')
        self.assertEqual(cm.exception.messages[0], u'This field cannot be null.')
    
    
###############################################################################
####################################################### Model multi tag field
###############################################################################
####### tagulous.models.managers.BaseTagManager
####### tagulous.models.managers.SingleTagManager
####### tagulous.models.descriptors.BaseTagDescriptor
####### tagulous.models.descriptors.SingleTagDescriptor
####### tagulous.models.fields.SingleTagField
####### tagulous.models.fields.SingleTagField
###############################################################################

class ModelMultiTagFieldTest(TagTestManager, TestCase):
    """
    Test model TagField
    """
    manage_models = [
        test_models.TagModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.TagModel.tags.tag_model
        self.tag_field = test_models.TagModel.tags
    
    def test_descriptor(self):
        "Check TagDescriptor is in place"
        self.assertTrue(isinstance(
            self.tag_field, tag_models.TagDescriptor
        ))
    
    def test_tag_table(self):
        "Check the tag table exists"
        self.assertTrue(issubclass(self.tag_field.field.rel.to, tag_models.TagModel))
        self.assertTrue(issubclass(self.tag_field.tag_model, tag_models.TagModel))
    
    def test_empty_value(self):
        "Check the descriptor returns a TagRelatedManager"
        t1 = self.create(test_models.TagModel, name="Test")
        self.assertInstanceEquals(t1, name="Test")
        
        # Check the TagDescriptor is returning a TagRelatedManager
        self.assertEqual(t1.tags.__class__.__name__, 'TagRelatedManager')
        
        # Check it also has a reference to the correct model
        self.assertEqual(t1.tags.tag_model, self.tag_model)
    
    def test_tag_assignment(self):
        "Check a tag string can be assigned to the descriptor and returned"
        t1 = self.create(test_models.TagModel, name="Test")
        t1.tags = 'django, javascript'
        
        # ++ do we want to treat as m2m? if so, has to be set after save
        # ++ or do we want to treat as model value? if so, store in cache and
        #   commit on save, like singletagfield
        # ++ quite like that idea - then it makes sense in .create, .get_or_create etc
        
        # Check they come back as expected
        self.assertEqual(t1.tags.get_tag_string(), 'django, javascript')
        self.assertEqual('%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(u'%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(len(t1.tags.get_tag_list()), 2)
        self.assertTrue('django' in t1.tags.get_tag_list())
        self.assertTrue('javascript' in t1.tags.get_tag_list())
        self.assertTagModel(self.tag_model, {
            'django':       1,
            'javascript':   1,
        })
    
    
    @unittest.skip('starting change')
    def test_tag_assignment_in_constructor(self):
        "Check a tag string can be passed in the constructor"
        t1 = test_models.TagModel(name="Test", title='Mr')
    
    
class OldModelTagFieldTestCase(TestCase, TagTestManager):
    def setUp(self):
        # Load initial tags for all models which have them
        tag_models.initial.model_initialise_tags(MultiTestModel)
        tag_models.initial.model_initialise_tags(CustomTestFirstModel)
        tag_models.initial.model_initialise_tags(CustomTestSecondModel)
        
    @unittest.skip('converting')
    def test_instances_correct(self):
        """
        Create instances and check that basic tags work
        """
        # Add some tags using the string converter
        test1.tags = 'django, javascript'
        
        # Check they come back as expected
        self.assertEqual(test1.tags.get_tag_string(), 'django, javascript')
        self.assertEqual('%s' % test1.tags, test1.tags.get_tag_string())
        self.assertEqual(u'%s' % test1.tags, test1.tags.get_tag_string())
        self.assertEqual(len(test1.tags.get_tag_list()), 2)
        self.assertTrue('django' in test1.tags.get_tag_list())
        self.assertTrue('javascript' in test1.tags.get_tag_list())
        self.assertTagModel(tag_model, {
            'django':       1,
            'javascript':   1,
        })
        
        # Create another instance and check everything is ok
        test2 = TestModel(name="Second")
        test2.save()
        test2.tags = 'django, html'
        self.assertEqual(test1.tags.get_tag_string(), 'django, javascript')
        self.assertEqual(test2.tags.get_tag_string(), 'django, html')
        self.assertTagModel(tag_model, {
            'django':       2,
            'html':         1,
            'javascript':   1,
        })
        
        # Add a tag by changing tag string
        test2.tags = 'django, html, javascript'
        self.assertEqual(test1.tags.get_tag_string(), 'django, javascript')
        self.assertEqual(test2.tags.get_tag_string(), 'django, html, javascript')
        self.assertTagModel(tag_model, {
            'django':       2,
            'html':         1,
            'javascript':   2,
        })
        
        # Add a tag manually
        test1.tags.add(
            tag_model.objects.get(name='html')
        )
        self.assertEqual(test1.tags.get_tag_string(), 'django, html, javascript')
        self.assertEqual(test2.tags.get_tag_string(), 'django, html, javascript')
        self.assertTagModel(tag_model, {
            'django':       2,
            'html':         2,
            'javascript':   2,
        })
        
        # Remove a tag manually
        test1.tags.remove(
            tag_model.objects.get(name='html')
        )
        self.assertEqual(test1.tags.get_tag_string(), 'django, javascript')
        self.assertEqual(test2.tags.get_tag_string(), 'django, html, javascript')
        self.assertTagModel(tag_model, {
            'django':       2,
            'html':         1,
            'javascript':   2,
        })
        
        # Remove a tag by changing tag string, and reduce its count to 0
        test2.tags = 'django, javascript'
        self.assertEqual(test1.tags.get_tag_string(), 'django, javascript')
        self.assertEqual(test2.tags.get_tag_string(), 'django, javascript')
        self.assertTagModel(tag_model, {
            'django':       2,
            'javascript':   2,
        })
        
        # Delete a test instance and check the counts are updated
        test2.delete()
        self.assertTagModel(tag_model, {
            'django':       1,
            'javascript':   1,
        })
        
        # Make django tag protected
        tag_django = tag_model.objects.get(name='django')
        tag_django.protected = True
        tag_django.save()
        
        # Delete other test instance and check django persisted
        test1.delete()
        self.assertTagModel(tag_model, {
            'django':       0,
        })
        
        
        #
        # Test the different ways of assigning tags using __set__
        #
        
        test3 = TestModel(name="Third")
        test3.save()
        test4 = TestModel(name="Fourth")
        test4.save()
        
        # Check setting tags with a list/tuple of tag names
        test3.tags = ['javascript', 'html', 'css']
        self.assertEqual(test3.tags.get_tag_string(), 'css, html, javascript')
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   1,
            'html':         1,
            'css':          1,
        })
        
        # Clear with empty list
        test3.tags = []
        self.assertEqual(test3.tags.get_tag_string(), '')
        self.assertTagModel(tag_model, {
            'django':       0,
        })
        
        # Single item
        test3.tags = ['javascript']
        self.assertEqual(test3.tags.get_tag_string(), 'javascript')
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   1,
        })
        
        # Test setting in one instance doesn't break another instance
        test4.tags = ['javascript', 'html']
        self.assertEqual(test4.tags.get_tag_string(), 'html, javascript')
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   2,
            'html':         1,
        })
        
        # Check that empty string also clears
        test4.tags = ''
        self.assertEqual(test4.tags.get_tag_string(), '')
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   1,
        })
        
        # Reset by checking clear()
        test3.tags.clear()
        test4.tags.clear()
        self.assertEqual(test3.tags.get_tag_string(), '')
        self.assertTagModel(tag_model, {
            'django':       0,
        })
        
        # Manually create a tag
        javascript_tag = tag_model.objects.create(name='javascript')
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   0,
        })
        
        # Check setting tags with a list/tuple of a TagModel instance
        test3.tags = [tag_model.objects.get(name='javascript')]
        self.assertEqual(test3.tags.get_tag_string(), 'javascript')
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   1,
        })
        
        # Make javascript protected and clear tags
        javascript_tag = tag_model.objects.get(name='javascript')
        javascript_tag.protected = True
        javascript_tag.save()
        self.assertTagModel(tag_model, {
            'django':       0,
            'javascript':   1,
        })
        test3.tags.clear()
        
        # Check setting with multiple instances
        test3.tags = [
            tag_model.objects.get(name='django'),
            tag_model.objects.get(name='javascript')
        ]
        self.assertTagModel(tag_model, {
            'django':       1,
            'javascript':   1,
        })
        
        # Check a queryset
        test4.tags = tag_model.objects.all()
        self.assertTagModel(tag_model, {
            'django':       2,
            'javascript':   2,
        })
    
        
    def test_multipletags_correct(self):
        """
        Test that multiple tags on a model work
        Also test tag arguments
        """
        #
        # Test initial
        #
        
        # Test that the initial values are in the database
        self.assertTagModel(MultiTestModel.tagset1.tag_model, {})
        self.assertTagModel(MultiTestModel.tagset2.tag_model, {
            'red':      0,
            'green':    0,
            'blue':     0,
        })
        self.assertTagModel(MultiTestModel.tagset3.tag_model, {
            'Adam':   0,
        })
        
        # Test set and get on multiple fields
        test1 = MultiTestModel.objects.create(name='First')
        test1.tagset1 = 'django, html'
        test1.tagset2 = 'blue, green, red'
        test1.tagset3 = 'Adam, Brian, Chris'
        self.assertEqual(test1.tagset1.get_tag_string(), 'django, html')
        self.assertEqual(test1.tagset2.get_tag_string(), 'blue, green, red')
        self.assertEqual(test1.tagset3.get_tag_string(), 'Adam, Brian, Chris')
        
        # Test tagset1 protect_all
        test1.tagset1.clear()
        self.assertEqual(test1.tagset1.get_tag_string(), '')
        self.assertTagModel(MultiTestModel.tagset1.tag_model, {
            'django':   0,
            'html':     0,
        })
        
        
        #
        # Other settings
        #
        test2 = MultiTestModel.objects.create(name='Second')
        
        # Test tagset1 case_sensitive
        test2.tagset1 = 'Django, HTML'
        self.assertEqual(test2.tagset1.get_tag_string(), 'Django, HTML')
        self.assertTagModel(MultiTestModel.tagset1.tag_model, {
            'django':   0,
            'html':     0,
            'Django':   1,
            'HTML':     1,
        })
        
        # Test tagset2 force_lowercase
        test2.tagset2 = 'BLUE, GREEN, YELLOW'
        self.assertEqual(test2.tagset2.get_tag_string(), 'blue, green, yellow')
        self.assertTagModel(MultiTestModel.tagset2.tag_model, {
            'red':      1,
            'green':    2,
            'blue':     2,
            'yellow':   1,
        })
        
        # Test tagset3 case insensitive
        test2.tagset3 = 'adam, CHRIS'
        self.assertEqual(test2.tagset3.get_tag_string(), 'Adam, Chris')
        self.assertTagModel(MultiTestModel.tagset3.tag_model, {
            'Adam':     2,
            'Brian':    1,
            'Chris':    2,
        })
        
        
        #
        # Test protect_initial
        #
        
        # Test protect_initial=True
        test1.tagset2.clear()
        test2.tagset2 = 'pink'
        self.assertEqual(test1.tagset2.get_tag_string(), '')
        self.assertEqual(test2.tagset2.get_tag_string(), 'pink')
        # Should leave initials
        self.assertTagModel(MultiTestModel.tagset2.tag_model, {
            'red':      0,
            'green':    0,
            'blue':     0,
            'pink':     1,
        })
        
        # Test protect_initial=False
        test1.tagset3.clear()
        test2.tagset3.clear()
        self.assertEqual(test1.tagset3.get_tag_string(), '')
        self.assertEqual(test2.tagset3.get_tag_string(), '')
        # Should remove initials
        self.assertTagModel(MultiTestModel.tagset3.tag_model, {})
        
    def test_custom_model(self):
        """
        Test custom tag models
        """
        # Make sure the test model is correct
        self.assertEqual(CustomTestFirstModel.tags.tag_model, CustomTestTagModel)
        self.assertEqual(CustomTestSecondModel.tags.tag_model, CustomTestTagModel)
        
        # Check options found correctly (protect_all, initial)
        self.assertEqual(CustomTestTagModel.tag_options.protect_all, True)
        self.assertEqual(len(CustomTestTagModel.tag_options.initial), 2)
        self.assertTrue('django' in CustomTestTagModel.tag_options.initial)
        self.assertTrue('javascript' in CustomTestTagModel.tag_options.initial)
        self.assertTagModel(CustomTestTagModel, {
            'django':   0,
            'javascript': 0,
        })
        
        # Create test item with test tags in both models
        test1 = CustomTestFirstModel.objects.create(name='first')
        test1.tags = 'django, html'
        test2 = CustomTestSecondModel.objects.create(name='second')
        test2.tags = 'css, javascript'
        
        # Check everything is ok
        self.assertEqual(test1.tags.get_tag_string(), 'django, html')
        self.assertEqual(test2.tags.get_tag_string(), 'css, javascript')
        self.assertTagModel(CustomTestTagModel, {
            'django':   1,
            'html':     1,
            'css':      1,
            'javascript': 1,
        })
        
        # Clear and check that they've been emptied but protect_all is obeyed
        test1.tags.clear()
        test2.tags.clear()
        self.assertEqual(test1.tags.get_tag_string(), '')
        self.assertEqual(test2.tags.get_tag_string(), '')
        self.assertTagModel(CustomTestTagModel, {
            'django':   0,
            'html':     0,
            'css':      0,
            'javascript': 0,
        })
        
    def test_tag_comparison(self):
        """
        Test that tag comparison works
        """
        # Using MultiTestModel to test case
        #   tagset1     case_sensitive=True
        #   tagset2     force_lowercase=True
        #   tagset3     case_sensitive=False, force_lowercase=False
        # Set up initial test
        test1 = MultiTestModel.objects.create(name='CmpOne')
        test1.tagset1 = 'django, html'
        test1.tagset2 = 'blue, green, red'
        test1.tagset3 = 'Adam, Brian, Chris'
        
        # Test case sensitive match
        self.assertEqual(test1.tagset1, 'django, html')
        self.assertNotEqual(test1.tagset1, 'django, HTML')
        self.assertNotEqual(test1.tagset1, 'Django, html')
        self.assertNotEqual(test1.tagset1, 'django')
        self.assertNotEqual(test1.tagset1, 'django, html, javascript')
        
        # Test lowercase match
        self.assertEqual(test1.tagset2, 'blue, green, red')
        self.assertEqual(test1.tagset2, 'Blue, grEEn, RED')
        self.assertNotEqual(test1.tagset2, 'blue, green')
        self.assertNotEqual(test1.tagset2, 'blue, green, red, yellow')
        
        # Test tags with neither case_sensitive nor force_lowercase
        self.assertEqual(test1.tagset3, 'Adam, Brian, Chris')
        self.assertEqual(test1.tagset3, 'adam, brian, chris')
        self.assertEqual(test1.tagset3, 'ADAM, BRIAN, CHRIS')
        self.assertNotEqual(test1.tagset3, 'Adam, Brian')
        self.assertNotEqual(test1.tagset3, 'Adam, Brian, Chris, David')
        
        # Check strings are parsed for matching
        self.assertEqual(test1.tagset1, 'html django')
        self.assertEqual(test1.tagset2, 'red green blue')
        self.assertEqual(test1.tagset3, 'chris adam brian')
        
        # ++ Test comparing against a list
        # ++ Test comparing one model field against another
        # ++ Test single tag manager
        



###############################################################################
####################################################### Model field order
###############################################################################
####### tagulous.models.fields.SingleTagField
####### tagulous.models.fields.TagField
###############################################################################


class ModelFieldOrderTest(TagTestManager, TestCase):
    """
    Test model SingleTagField order
    """
    manage_models = [
        test_models.MixedOrderTest,
    ]
    
    def test_order_correct(self):
        """
        Check that the order of the non-ManyToMany fields is correct
        This is to check that Django internals haven't changed significantly
        """
        # Check the ordering is as expected
        ##38# ++ Change for Django 1.8?
        opts = test_models.MixedOrderTest._meta
        local_fields = sorted(opts.concrete_fields +  opts.many_to_many)
        expected_fields = [
            # Auto pk 'id'
            'id',
            # Defined fields
            'char1', 'fk1', 'char2', 'single1', 'char3', 'm2m1', 'char4',
            'multi1', 'char5', 'm2m2', 'char6', 'fk2', 'char7',
        ]
        self.assertEqual(len(local_fields), len(expected_fields))
        for i in range(len(local_fields)):
            self.assertEqual(local_fields[i].name, expected_fields[i])



###############################################################################
######################################################################## Forms
###############################################################################

class OldFormTest(TestCase, TagTestManager):
    def setUp(self):
        # Load initial tags for all models which have them
        tag_models.initial.model_initialise_tags(test_models.SingleFormTest)

    def test_form_field(self):
        """
        Test the form field basics
        """
        self.assertTrue(tag_forms.SingleTagField(required=True).required)
        self.assertTrue(tag_forms.SingleTagField(required=True).widget.is_required)
        self.assertFalse(tag_forms.SingleTagField(required=False).required)
        self.assertFalse(tag_forms.SingleTagField(required=False).widget.is_required)
        self.assertTrue(tag_forms.SingleTagField().required)
        self.assertTrue(tag_forms.SingleTagField().widget.is_required)

    def test_single_model_formfield(self):
        """
        Test that model.SingleTagField.formfield works correctly
        """
        # Check that the model fields are generated correctly
        tag1_field = test_models.SingleFormTest._meta.get_field('tag1').formfield()
        tag2_field = test_models.SingleFormTest._meta.get_field('tag2').formfield()
        tag3_field = test_models.SingleFormTest._meta.get_field('tag3').formfield()
        self.assertTrue(isinstance(tag1_field, tag_forms.SingleTagField))
        self.assertTrue(isinstance(tag2_field, tag_forms.SingleTagField))
        self.assertTrue(isinstance(tag3_field, tag_forms.SingleTagField))
        
        # Check field options
        self.assertTrue(isinstance(tag1_field.tag_options, tag_models.TagOptions))
        self.assertTrue(isinstance(tag2_field.tag_options, tag_models.TagOptions))
        self.assertTrue(isinstance(tag3_field.tag_options, tag_models.TagOptions))
        self.assertEqual(tag1_field.tag_options.case_sensitive, True)
        self.assertEqual(tag2_field.tag_options.force_lowercase, True)
        self.assertEqual(tag3_field.tag_options.case_sensitive, False)
        self.assertEqual(tag3_field.tag_options.force_lowercase, False)
    
    def test_form_field_output(self):
        # Check field output
        self.assertFieldOutput(tag_forms.SingleTagField,
            valid={
                'Mr': 'Mr',
                'Mr, Mrs': 'Mr, Mrs',
            },
            invalid={
                '"': [u'This field cannot contain the " character'],
            },
            empty_value=None
        )
        self.assertFieldOutput(tag_forms.SingleTagField,
            field_kwargs={
                'tag_options': tag_models.TagOptions(
                    force_lowercase=True
                )
            },
            valid={
                'Mr': 'mr',
                'Mr, Mrs': 'mr, mrs',
            },
            invalid={
                '"': [u'This field cannot contain the " character'],
            },
            empty_value=None
        )
        
    def test_single_model_form(self):
        """
        Test that a model form with a SingleTagField functions correctly
        """
        # Check that the form is created correctly
        form = test_forms.SingleFormTest()
        
        # Check the form media
        media = form.media
        for js in tag_settings.AUTOCOMPLETE_JS:
            self.assertTrue(js in media._js)
        for grp, files in tag_settings.AUTOCOMPLETE_CSS.items():
            self.assertTrue(grp in media._css)
            for css in files:
                self.assertTrue(css in media._css[grp])
        
        # ++
        
