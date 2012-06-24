from unittest import TestCase as UnitTestCase

from django.db import models
from django.core import exceptions
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

from tagulous.models import \
    TagModel, TagDescriptor, \
    RelatedManagerTagMixin, SingleTagDescriptor
    
from tagulous.tests_app.models import \
    TestModel, OrderTestModel, MultiTestModel, CustomTestTagModel, \
    CustomTestFirstModel, CustomTestSecondModel, \
    SingleTestModel, SingleOrderTestModel, \
    SingleRequiredTestModel, SingleOptionalTestModel

class TestModelTestCase(TestCase):
    
    def test_model_correct(self):
        """
        Test that the tag model is created correctly
        """
        # Check that the TagDescriptor is in place
        self.assertTrue(isinstance(TestModel.tags, TagDescriptor))
        
        # Check that the tag table exists
        self.assertTrue(issubclass(TestModel.tags.field.rel.to, TagModel))
        self.assertTrue(issubclass(TestModel.tags.model, TagModel))
    
    def test_single_model_correct(self):
        """
        Test that the single tag model is created correctly
        """
        # Check SingleTagDescriptor is in place
        self.assertTrue(isinstance(SingleTestModel.title, SingleTagDescriptor))
        
        # Check the tag table exists
        self.assertTrue(issubclass(SingleTestModel.title.model, TagModel))
    
    def test_field_order_correct(self):
        """
        Test that the order of ManyToMany fields is correct
        This is to check that Django internals haven't changed significantly
        """
        # Make sure that there haven't been significant changes to the way
        # fields are ordered. If this test fails, see the developer notes in
        # Tagulous.models.TagField for possible solutions.
        self.assertTrue(hasattr(models.fields.Field, 'creation_counter'))
        
        # Check the ordering is as expected
        self.assertEqual(len(OrderTestModel._meta.local_many_to_many), 3)
        self.assertEqual(OrderTestModel._meta.local_many_to_many[0].name, 'first')
        self.assertEqual(OrderTestModel._meta.local_many_to_many[1].name, 'tags')
        self.assertEqual(OrderTestModel._meta.local_many_to_many[2].name, 'second')
    
    def test_single_field_order_correct(self):
        """
        Test that the order of the non-ManyToMany fields is correct
        This is to check that Django internals haven't changed significantly
        """
        # Check the ordering is as expected
        # 6 + auto pk 'id'
        self.assertEqual(len(SingleOrderTestModel._meta.local_fields), 7)
        self.assertEqual(SingleOrderTestModel._meta.local_fields[0].name, 'id')
        self.assertEqual(SingleOrderTestModel._meta.local_fields[1].name, 'first')
        self.assertEqual(SingleOrderTestModel._meta.local_fields[2].name, 'second')
        self.assertEqual(SingleOrderTestModel._meta.local_fields[3].name, 'third')
        self.assertEqual(SingleOrderTestModel._meta.local_fields[4].name, 'tag')
        self.assertEqual(SingleOrderTestModel._meta.local_fields[5].name, 'fourth')
        self.assertEqual(SingleOrderTestModel._meta.local_fields[6].name, 'fifth')
    
    def test_instances_correct(self):
        """
        Create instances and check that basic tags work
        """
        # Get tag model
        tag_model = TestModel.tags.model
        
        # Check basic model still works (!)
        test1 = TestModel(name="First")
        test1.save()
        self.assertEqual(test1.name, 'First')
        
        # Check the TagDescriptor is returning a TagRelatedManager
        self.assertEqual(test1.tags.__class__.__name__, 'TagRelatedManager')
        
        # Check it also has a reference to the correct model
        self.assertEqual(test1.tags.model, tag_model)
        
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
        
        # Remove a test instance and check the counts are updated
        test2.delete()
        self.assertTagModel(tag_model, {
            'django':       1,
            'javascript':   1,
        })
        
        # Make django tag protected
        tag_django = tag_model.objects.get(name='django')
        tag_django.protected = True
        tag_django.save()
        
        # Remove other test instance and check django persisted
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
    
    def test_single_instances_correct(self):
        """
        Create instances and check that basic single tag works
        """
        # Get tag model
        tag_model = SingleTestModel.title.model
        
        # Check basic model still works (!)
        test1 = SingleTestModel(name="First")
        test1.save()
        self.assertEqual(test1.name, 'First')
        
        # Check the SingleTagDescriptor is returning None as expected
        self.assertEqual(test1.title, None)
        
        # Set a tag and check it is available before saving
        test1.title = 'Mr'
        self.assertEqual(test1.title.__class__, SingleTestModel.title.model)
        self.assertEqual(test1.title.name, 'Mr')
        self.assertEqual('%s' % test1.title, 'Mr')
        self.assertEqual(u'%s' % test1.title, 'Mr')
        self.assertTagModel(tag_model, {})
        
        # Check it is available after saving
        test1.save()
        self.assertEqual(test1.title.__class__, SingleTestModel.title.model)
        self.assertEqual(test1.title.name, 'Mr')
        self.assertEqual('%s' % test1.title, 'Mr')
        self.assertEqual(u'%s' % test1.title, 'Mr')
        self.assertTagModel(tag_model, {
            'Mr':   1,
        })
        
        # Check setting a title before saving works
        test2 = SingleTestModel(name="Second", title='Mrs')
        test2.save()
        self.assertEqual(test2.name, 'Second')
        self.assertEqual(test2.title.name, 'Mrs')
        self.assertTagModel(tag_model, {
            'Mr':   1,
            'Mrs':  1,
        })
        
        # Set a title using a tag object, and check tag is incremented
        tagMr = test1.title
        tagMrs = test2.title
        test3 = SingleTestModel(name="Third", title=tagMr)
        test3.save()
        self.assertEqual(test3.name, 'Third')
        self.assertEqual(test3.title.name, 'Mr')
        self.assertTagModel(tag_model, {
            'Mr':   2,
            'Mrs':  1,
        })
        
        # Change a title using a string, and check tag counts are updated
        test3.title = 'Mrs'
        test3.save()
        self.assertEqual(test3.name, 'Third')
        self.assertEqual(test3.title.name, 'Mrs')
        self.assertTagModel(tag_model, {
            'Mr':   1,
            'Mrs':  2,
        })
        
        # Change a title using a tag object and check tag counts are updated
        test3.title = tagMr
        test3.save()
        self.assertEqual(test3.name, 'Third')
        self.assertEqual(test3.title.name, 'Mr')
        self.assertTagModel(tag_model, {
            'Mr':   2,
            'Mrs':  1,
        })
        
        # Remove a tag by changing to another and reducing its count to 0
        test2.title = tagMr
        test2.save()
        self.assertTagModel(tag_model, {
            'Mr':   3,
        })
        
        # Decrement a tag by deleting an instance
        test3.delete()
        self.assertTagModel(tag_model, {
            'Mr':   2,
        })
        
        # Change the value, not saving, then delete, updating the count of
        # the old tag, but leaving the correct new tag on the object
        test2.title = "Mrs"
        self.assertEqual(test2.title.name, 'Mrs')
        self.assertTagModel(tag_model, {
            'Mr':   2,
        })
        test2.delete()
        self.assertEqual(test2.title.name, 'Mrs')
        
        # Remove a tag by deleting an instance
        test1.delete()
        self.assertTagModel(tag_model, {})
        
        # Re-save a deleted tag
        self.assertEqual(test1.title.name, 'Mr')
        self.assertTagModel(tag_model, {})
        test1.save()
        self.assertEqual(test1.title.name, 'Mr')
        self.assertTagModel(tag_model, {
            'Mr':   1,
        })
        
        # Check that multiple unsaved changes work
        test1.title = 'Dr'
        self.assertEqual(test1.title.name, 'Dr')
        self.assertTagModel(tag_model, {'Mr': 1,})
        test1.title = 'Ms'
        self.assertEqual(test1.title.name, 'Ms')
        self.assertTagModel(tag_model, {'Mr': 1,})
        test1.save()
        self.assertTagModel(tag_model, {
            'Ms':   1,
        })
        test1.title = 'Mr'
        self.assertTagModel(tag_model, {
            'Ms':   1,
        })
        test1.save()
        self.assertTagModel(tag_model, {
            'Mr':   1,
        })
        
        # Make two unsaved changes at once
        test2.save()
        self.assertTagModel(tag_model, {
            'Mr':   1,
            'Mrs':  1,
        })
        test1.title = 'Dr'
        test2.title = 'Ms'
        self.assertEqual(test1.title.name, 'Dr')
        self.assertEqual(test2.title.name, 'Ms')
        self.assertTagModel(tag_model, {
            'Mr':   1,
            'Mrs':  1,
        })
        test1.save()
        test2.save()
        self.assertTagModel(tag_model, {
            'Dr':   1,
            'Ms':   1,
        })
        
        # Check that loading works with SingleTagManager
        test1 = SingleTestModel.objects.get(name="First")
        self.assertEqual(test1.title.name, 'Dr')
        self.assertTagModel(tag_model, {
            'Dr':   1,
            'Ms':   1,
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
        self.assertTagModel(MultiTestModel.tagset1.model, {})
        self.assertTagModel(MultiTestModel.tagset2.model, {
            'red':      0,
            'green':    0,
            'blue':     0,
        })
        self.assertTagModel(MultiTestModel.tagset3.model, {
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
        self.assertTagModel(MultiTestModel.tagset1.model, {
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
        self.assertTagModel(MultiTestModel.tagset1.model, {
            'django':   0,
            'html':     0,
            'Django':   1,
            'HTML':     1,
        })
        
        # Test tagset2 force_lowercase
        test2.tagset2 = 'Blue, grEEn'
        self.assertEqual(test2.tagset2.get_tag_string(), 'blue, green')
        self.assertTagModel(MultiTestModel.tagset2.model, {
            'red':      1,
            'green':    2,
            'blue':     2,
        })
        
        # Test tagset3 case insensitive
        test2.tagset3 = 'adam, CHRIS'
        self.assertEqual(test2.tagset3.get_tag_string(), 'Adam, Chris')
        self.assertTagModel(MultiTestModel.tagset3.model, {
            'Adam':     2,
            'Brian':    1,
            'Chris':    2,
        })
        
        
        #
        # Test protect_initial
        #
        
        # Test protect_initial=True
        test1.tagset2.clear()
        test2.tagset2 = 'yellow'
        self.assertEqual(test1.tagset2.get_tag_string(), '')
        self.assertEqual(test2.tagset2.get_tag_string(), 'yellow')
        # Should leave initials
        self.assertTagModel(MultiTestModel.tagset2.model, {
            'red':      0,
            'green':    0,
            'blue':     0,
            'yellow':   1,
        })
        
        # Test protect_initial=False
        test1.tagset3.clear()
        test2.tagset3.clear()
        self.assertEqual(test1.tagset3.get_tag_string(), '')
        self.assertEqual(test2.tagset3.get_tag_string(), '')
        # Should remove initials
        self.assertTagModel(MultiTestModel.tagset3.model, {})
        
    def test_custom_model(self):
        """
        Test custom tag models
        """
        # Make sure the test model is correct
        self.assertEqual(CustomTestFirstModel.tags.model, CustomTestTagModel)
        self.assertEqual(CustomTestSecondModel.tags.model, CustomTestTagModel)
        
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
        
    def test_single_exceptions(self):
        """
        Test that correct exceptions are raised by SingleTagField
        """
        # Check optional field saves without exception
        opt1 = SingleOptionalTestModel(name="First")
        opt1.save()
        
        # Check required field raises exception
        with self.assertRaises(exceptions.ValidationError) as cm:
            test1 = SingleRequiredTestModel(name="First")
            test1.save()
        the_exception = cm.exception
        field = SingleRequiredTestModel._meta.get_field_by_name('tag')[0]
        self.assertEqual(the_exception.messages[0], u'This field cannot be null.')
        
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
        print "Tag model: %s" % field.model
        for tag in field.model.objects.all():
            print '%s: %d' % (tag.name, tag.count)
        print "-=-=-=-=-=-"
        
        