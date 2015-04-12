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
    MultiTestModel, CustomTestTagModel, \
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
    
    def assertInstanceEqual(self, instance, **kwargs):
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





####### # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
####### # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
####### # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class OldModelTagFieldTestCase(TestCase, TagTestManager):
    def setUp(self):
        # Load initial tags for all models which have them
        tag_models.initial.model_initialise_tags(MultiTestModel)
        tag_models.initial.model_initialise_tags(CustomTestFirstModel)
        tag_models.initial.model_initialise_tags(CustomTestSecondModel)
        
       
    @unittest.skip('converting') 
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
        
    @unittest.skip('converting')
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
        
    @unittest.skip('converting')
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
        
