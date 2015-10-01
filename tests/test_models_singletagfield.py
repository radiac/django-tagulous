"""
Tagulous test: Model SingleTagField

Modules tested:
    tagulous.models.managers.SingleTagManager
    tagulous.models.descriptors.BaseTagDescriptor
    tagulous.models.descriptors.SingleTagDescriptor
    tagulous.models.fields.BaseTagField
    tagulous.models.fields.SingleTagField
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from tests.lib import *


class ModelSingleTagFieldTest(TagTestManager, TestCase):
    """
    Test model SingleTagField
    """
    manage_models = [
        test_models.SingleTagFieldModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.SingleTagFieldModel.title.tag_model
        self.tag_field = test_models.SingleTagFieldModel.title
    
    def test_descriptor(self):
        "Check SingleTagDescriptor is in place"
        self.assertIsInstance(
            self.tag_field, tag_models.SingleTagDescriptor
        )
    
    def test_tag_table(self):
        "Check the tag table exists"
        self.assertTrue(issubclass(
            self.tag_model, tag_models.TagModel
        ))
        
    def test_empty_value(self):
        "Check the descriptor returns None for no value"
        t1 = self.create(test_models.SingleTagFieldModel, name="Test")
        self.assertInstanceEqual(t1, name="Test", title=None)
        self.assertTagModel(self.tag_model, {})

    def test_tag_assign_in_constructor(self):
        "Check a tag string can be set in the constructor"
        t1 = test_models.SingleTagFieldModel(name="Test", title='Mr')
        t1.save()
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_assign_by_object_in_constructor(self):
        "Check a tag object can be passed in the constructor"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel(name='Test 2', title=t1.title)
        t2.save()
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
    
    def test_tag_assign_in_object_create(self):
        "Check a tag string can be passed in object.create"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test', title='Mr')
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_assign_by_object_in_object_create(self):
        "Check a tag object can be passed in object.create"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title=t1.title)
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
    
    def test_tag_assign_in_object_get_or_create_true(self):
        """
        Check a tag string can be passed in object.get_or_create, when object
        does not exist
        """
        t1, state = test_models.SingleTagFieldModel.objects.get_or_create(
            name='Test', title='Mr',
        )
        self.assertEqual(state, True)
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_tag_assign_in_object_get_or_create_false(self):
        """
        Check a tag string can be passed in object.get_or_create, when object
        does exist
        """
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test', title='Mr')
        t2, state = test_models.SingleTagFieldModel.objects.get_or_create(
            name='Test', title='Mr',
        )
        self.assertEqual(state, False)
        self.assertEqual(t1.pk, t2.pk)
        self.assertEqual(t1.name, t2.name)
        self.assertEqual(t2.name, 'Test')
        self.assertEqual(t2.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
            
    def test_tag_assign_by_string(self):
        "Check a tag string can be assigned to descriptor and returned"
        t1 = self.create(test_models.SingleTagFieldModel, name="Test")
        t1.title = 'Mr'
        
        # Returned before save
        self.assertEqual(t1.title.__class__, self.tag_model)
        self.assertEqual(t1.title.name, 'Mr')
        self.assertEqual(six.text_type(t1.title), 'Mr')
        self.assertTagModel(self.tag_model, {})
        
        # Returned after save
        t1.save()
        self.assertEqual(t1.title.__class__, self.tag_model)
        self.assertEqual(t1.title.name, 'Mr')
        self.assertEqual(six.text_type(t1.title), 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_assign_by_object(self):
        """
        Check a tag object can be assigned to a SingleTagfield, and that its
        tag count is incremented
        """
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel(name='Test 2')
        t2.title = t1.title
        t2.save()
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t2.name, 'Test 2')
        self.assertEqual(six.text_type(t1.title), 'Mr')
        self.assertEqual(six.text_type(t2.title), 'Mr')
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
    
    def test_assign_string_empty(self):
        "Check an empty string can clear a SingleTagField"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        self.assertInstanceEqual(t1, name='Test 1', title='Mr')
        t1.title = ''
        t1.save()
        self.assertInstanceEqual(t1, name='Test 1', title=None)
        self.assertTagModel(self.tag_model, {})
    
    def test_assign_none(self):
        "Check assigning None can clear a SingleTagField"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        self.assertInstanceEqual(t1, name='Test 1', title='Mr')
        t1.title = None
        t1.save()
        self.assertInstanceEqual(t1, name='Test 1', title=None)
        self.assertTagModel(self.tag_model, {})
    
    def test_assign_string_quotes(self):
        "Check that a tag can contain quotes"
        # Check it saves ok
        t1 = test_models.SingleTagFieldModel.objects.create(
            name='Test 1', title='"One", Two"',
        )
        self.assertInstanceEqual(t1, name='Test 1', title='"One", Two"')
        
        # Check it loads ok
        t2 = test_models.SingleTagFieldModel.objects.get(pk=t1.pk)
        self.assertInstanceEqual(t2, name='Test 1', title='"One", Two"')
    
    def test_tag_assign_same(self):
        "Check that setting the same tag doesn't make a change"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        tag = t1.title
        self.assertEqual(tag, 'Mr')
        
        # Access the manager via the cache to watch changed state
        self.assertIsInstance(t1._title_tagulous, tag_models.SingleTagManager)
        self.assertFalse(t1._title_tagulous.changed, 'tag has changed')
        t1.title = 'Mr'
        self.assertFalse(t1._title_tagulous.changed, 'tag has changed')
        
    def test_change_decreases_count(self):
        "Check a tag string changes the count"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title=t1.title)
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
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title=t1.title)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
        t2.delete()
        self.assertInstanceEqual(t1, name='Test 1', title='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_count_zero_deletes_tag(self):
        "Check a count of 0 deletes an unprotected tag"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
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
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title='Mrs')
        self.assertEqual(six.text_type(t1.title.name), 'Mr')
        self.assertEqual(six.text_type(t2.title.name), 'Mrs')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        
        # Now change the title and delete without saving
        t1.title = 'Mrs'
        self.assertEqual(six.text_type(t1.title.name), 'Mrs')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        t1.delete()
        
        # Check the original tag 'Mr' was decremented (and deleted)
        self.assertTagModel(self.tag_model, {
            'Mrs': 1,
        })
        
        # But check that tagulous still thinks the tag is 'Mrs'
        self.assertEqual(six.text_type(t1.title.name), 'Mrs')
    
    def test_save_deleted_instance(self):
        """
        Check that a deleted tag in memory can be re-saved when the instance it
        is set on is deleted
        """
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        t1.delete()
        self.assertTagModel(self.tag_model, {})
        t1.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_save_deleted_tag(self):
        """
        Check that a delete tag in memory can be read and re-saved when it is
        deleted without the instance knowing about it
        """
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        self.tag_model.objects.all().delete()
        self.assertTagModel(self.tag_model, {})
        
        # Check it's still usable
        self.assertIsInstance(t1.title, tag_models.BaseTagModel)
        self.assertEqual(t1.title, 'Mr')
        
        # Check it can be re-saved
        t1.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_multiple_unsaved(self):
        "Check that there's no leak between unsaved objects"
        t1 = test_models.SingleTagFieldModel(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel(name='Test 1', title='Mrs')
        self.assertTagModel(self.tag_model, {})
        self.assertEqual(six.text_type(t1.title), 'Mr')
        self.assertEqual(six.text_type(t2.title), 'Mrs')
        t1.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        t2.save()
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
            'Mrs': 1,
        })
        self.assertEqual(six.text_type(t1.title), 'Mr')
        self.assertEqual(six.text_type(t2.title), 'Mrs')
    
    def test_load_instance(self):
        "Check that SingleTagField is loaded correctly"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.get(pk=t1.pk)
        self.assertIsInstance(t2.title, tag_models.BaseTagModel)
        self.assertEqual(t1.title, t2.title)
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })

    def test_descriptor_equal(self):
        "Check that descriptors evaluate to equal"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title='Mr')
        self.assertIsInstance(t1.title, self.tag_model)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertEqual(t1.title, t2.title)

    def test_descriptor_not_equal(self):
        "Check that descriptors evaluate to equal"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title='Mrs')
        self.assertIsInstance(t1.title, self.tag_model)
        self.assertNotEqual(t1.title, t2.title)
     
    def test_cascade_delete(self):
        "Check that deleting a tag deletes its related tagged items (by default)"
        model = test_models.SingleTagFieldModel
        t1 = model.objects.create(name='Test 1', title='Mr')
        t2 = model.objects.create(name='Test 2', title='Mr')
        t3 = model.objects.create(name='Test 3', title='Mrs')
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
            'Mrs': 1,
        })
        self.assertSequenceEqual(model.objects.all(), [t1, t2, t3])
        
        # Delete
        self.tag_model.objects.get(name='Mr').delete()
        self.assertTagModel(self.tag_model, {
            'Mrs': 1,
        })
        self.assertSequenceEqual(model.objects.all(), [t3])


###############################################################################
#######  Test invalid fields
###############################################################################

class ModelSingleTagFieldInvalidTest(TagTestManager, TransactionTestCase):
    """
    Test invalid model SingleTagField
    
    Use a TransactionTestCase so the apps will be reset
    """
    manage_models = [
        test_models.SingleTagFieldModel,
    ]
    
    def test_invalid_to_model(self):
        "Check that the to model has to be a TagModel subclass"
        with self.assertRaises(ValueError) as cm:
            class FailModel_invalid_to(models.Model):
                to_model = tag_models.SingleTagField(test_models.SingleTagFieldModel)
        self.assertEqual(
            six.text_type(cm.exception),
            "Tag model must be a subclass of TagModel"
        )
    
    def test_forbidden_to_field(self):
        "Check that to_field argument raises exception"
        with self.assertRaises(ValueError) as cm:
            class FailModel_forbidden_to(models.Model):
                to_field = tag_models.SingleTagField(to_field='fail')
        self.assertEqual(
            six.text_type(cm.exception),
            "Invalid argument 'to_field' for SingleTagField"
        )

    def test_forbidden_rel_class(self):
        "Check that rel_class argument raises exception"
        with self.assertRaises(ValueError) as cm:
            class FailModel_forbidden_rel(models.Model):
                rel_class = tag_models.SingleTagField(rel_class='fail')
        self.assertEqual(
            six.text_type(cm.exception),
            "Invalid argument 'rel_class' for SingleTagField"
        )

    def test_forbidden_max_count(self):
        "Check that max_count argument raises exception"
        with self.assertRaises(ValueError) as cm:
            class FailModel_forbidden_max_count(models.Model):
                max_count = tag_models.SingleTagField(max_count='fail')
        self.assertEqual(
            six.text_type(cm.exception),
            "Invalid argument 'max_count' for SingleTagField"
        )
    
    def test_value_from_object_none(self):
        "Check that value_from_object returns empty string instead of None"
        # Called by forms, but part of model, so test it here
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1')
        field = test_models.SingleTagFieldModel._meta.get_field('title')
        self.assertEqual(field.value_from_object(t1), '')
        

###############################################################################
#######  Test model field blank=True
###############################################################################

class ModelSingleTagFieldOptionalTest(TagTestManager, TestCase):
    """
    Test optional model SingleTagField
    """
    manage_models = [
        test_models.SingleTagFieldOptionalModel,
    ]
    def test_optional_save_missing(self):
        "Check an optional SingleTagField isn't required for save"
        # If it fails, it will return an exception
        t1 = test_models.SingleTagFieldOptionalModel(name='Test 1')
        t1.save()
        self.assertNotEqual(t1.pk, None)
    
    def test_optional_create_missing(self):
        "Check an optional SingleTagField isn't required for object.create"
        # If it fails, it will return an exception
        t1 = test_models.SingleTagFieldOptionalModel.objects.create(name='Test 1')
        self.assertNotEqual(t1.pk, None)


###############################################################################
####### Test model field blank=False
###############################################################################

class ModelSingleTagFieldRequiredTest(TagTestManager, TestCase):
    """
    Test required model SingleTagField
    """
    manage_models = [
        test_models.SingleTagFieldRequiredModel,
    ]
    def test_required_save_raises(self):
        "Check a required SingleTagField raises an exception when saved"
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.SingleTagFieldRequiredModel(name='Test')
            t1.save()
        self.assertEqual(cm.exception.messages[0], 'This field cannot be null.')
    
    def test_required_create_raises(self):
        "Check a required SingleTagField raises an exception in object.create"
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.SingleTagFieldRequiredModel.objects.create(name='Test')
        self.assertEqual(cm.exception.messages[0], 'This field cannot be null.')
    
    
###############################################################################
####### Test multiple SingleTagFields on a model
###############################################################################

class ModelSingleTagFieldMultipleTest(TagTestManager, TestCase):
    """
    Test multiple tag fields on a model
    """
    manage_models = [
        test_models.SingleTagFieldMultipleModel,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.SingleTagFieldMultipleModel
        self.tag_field_1 = test_models.SingleTagFieldMultipleModel.tag1
        self.tag_field_2 = test_models.SingleTagFieldMultipleModel.tag2
        self.tag_field_3 = test_models.SingleTagFieldMultipleModel.tag3
    
    def test_tag_models(self):
        self.assertTrue(issubclass(self.tag_field_1.tag_model, tag_models.TagModel))
        self.assertTrue(issubclass(self.tag_field_2.tag_model, tag_models.TagModel))
        self.assertTrue(issubclass(self.tag_field_3.tag_model, tag_models.TagModel))
        
    def test_separate_models(self):
        self.assertNotEqual(self.tag_field_1.tag_model, self.tag_field_2.tag_model)
        self.assertNotEqual(self.tag_field_1.tag_model, self.tag_field_3.tag_model)
        self.assertNotEqual(self.tag_field_2.tag_model, self.tag_field_3.tag_model)
    
    def test_model_names(self):
        self.assertEqual(
            self.tag_field_1.tag_model.__name__,
            '_Tagulous_SingleTagFieldMultipleModel_tag1'
        )
        self.assertEqual(
            self.tag_field_2.tag_model.__name__,
            '_Tagulous_SingleTagFieldMultipleModel_tag2'
        )
        self.assertEqual(
            self.tag_field_3.tag_model.__name__,
            '_Tagulous_SingleTagFieldMultipleModel_tag3'
        )
    
    def test_set_and_get(self):
        "Test multiple fields can be set and retrieved independently"
        t1 = self.create(
            self.test_model, name="Test 1",
            tag1='Mr', tag2='blue', tag3='adam',
        )
        t2 = self.create(
            self.test_model, name="Test 2",
            tag1='Mrs', tag2='green', tag3='brian',
        )
        t3 = self.create(
            self.test_model, name="Test 3",
            tag1='Ms', tag2='red', tag3='chris',
        )
        
        self.assertTagModel(self.tag_field_1, {
            'Mr':   1,
            'Mrs':  1,
            'Ms':   1,
        })
        self.assertTagModel(self.tag_field_2, {
            'blue': 1,
            'green': 1,
            'red':  1,
        })
        self.assertTagModel(self.tag_field_3, {
            'adam': 1,
            'brian': 1,
            'chris': 1,
        })
        
        self.assertInstanceEqual(t1, name="Test 1", tag1='Mr', tag2='blue', tag3='adam')
        self.assertInstanceEqual(t2, name="Test 2", tag1='Mrs', tag2='green', tag3='brian')
        self.assertInstanceEqual(t3, name="Test 3", tag1='Ms', tag2='red', tag3='chris')


###############################################################################
####### Test SingleTagField with string references to tag model
###############################################################################

class ModelSingleTagFieldStringTest(TagTestManager, TransactionTestCase):
    """
    Test SingleTagField which refers to its tag model with a string
    """
    manage_models = [
        test_models.MixedStringTo,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.MixedStringTo
        self.tag_field = self.test_model.singletag
        self.tag_model = test_models.MixedStringTagModel
    
    def test_to_model(self):
        "Check related model is correct"
        self.assertTrue(issubclass(self.tag_field.tag_model, tag_models.TagModel))
        if django.VERSION < (1, 9):
            self.assertEqual(self.tag_field.field.remote_field.to, self.tag_model)
        else:
            self.assertEqual(self.tag_field.field.remote_field.model, self.tag_model)
        self.assertEqual(self.tag_field.tag_model, self.tag_model)
    
    def test_tag_options(self):
        "Check tag options are available correctly"
        self.assertEqual(
            self.tag_field.tag_options, self.tag_model.tag_options
        )
        
    def test_use(self):
        "Test basic use of tag field"
        self.assertTagModel(self.tag_model, {})
        t1 = self.test_model.objects.create(name='Test 1', singletag='Mr')
        self.assertTagModel(self.tag_model, {
            'Mr':  1,
        })
        self.assertInstanceEqual(t1, name='Test 1', singletag='Mr')
        

class ModelSingleTagFieldSelfTest(TagTestManager, TransactionTestCase):
    """
    Test SingleTagField which refers to itself
    """
    manage_models = [
        test_models.MixedSelfTo,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.MixedSelfTo
        self.tag_field = self.test_model.alternate
    
    def test_to_model(self):
        "Check related model is correct"
        self.assertTrue(issubclass(self.tag_field.tag_model, tag_models.TagModel))
        if django.VERSION < (1, 9):
            self.assertEqual(self.tag_field.field.remote_field.to, self.test_model)
        else:
            self.assertEqual(self.tag_field.field.remote_field.model, self.test_model)
        self.assertEqual(self.tag_field.tag_model, self.test_model)
    
    def test_tag_options(self):
        "Check tag options are available correctly"
        self.assertEqual(
            self.tag_field.tag_options, self.test_model.tag_options
        )
        
    def test_use(self):
        "Test basic use of tag field"
        self.assertTagModel(self.test_model, {})
        t1 = self.test_model.objects.create(name='Test 1', alternate='mr')
        self.assertTagModel(self.test_model, {
            'mr':  1,
            'Test 1': 0,
        })
        self.assertInstanceEqual(t1, name='Test 1', alternate='mr')


###############################################################################
####### Test SingleTagField options
###############################################################################

class ModelSingleTagFieldOptionsTest(TagTestManager, TestCase):
    """
    Test single tag field options
    """
    manage_models = [
        test_models.SingleTagFieldOptionsModel,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.SingleTagFieldOptionsModel
    
    def test_initial_string(self):
        # Initial will have been loaded by TagTestManager
        self.assertTagModel(self.test_model.initial_string, {
            'Mr':   0,
            'Mrs':  0,
            'Ms':   0,
        })
        
    def test_initial_list(self):
        # Initial will have been loaded by TagTestManager
        self.assertTagModel(self.test_model.initial_list, {
            'Mr':   0,
            'Mrs':  0,
            'Ms':   0,
        })
    
    def test_protect_initial_true(self):
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Mr':   0,
        })
        
        t1 = self.create(self.test_model, name="Test 1", protect_initial_true='Mr')
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Mr':   1,
        })
        
        t1.protect_initial_true = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Mr':   0,
        })
        
    def test_protect_initial_false(self):
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Mr':   0,
        })
        
        t1 = self.create(self.test_model, name="Test 1", protect_initial_false='Mr')
        self.assertTagModel(self.test_model.protect_initial_false, {
            'Mr':   1,
        })
        
        t1.protect_initial_false = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_initial_false, {})
    
    def test_protect_all_true(self):
        t1 = self.create(self.test_model, name="Test 1", protect_all_true='Mr')
        self.assertTagModel(self.test_model.protect_all_true, {
            'Mr':   1,
        })
        
        t1.protect_all_true = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_all_true, {
            'Mr':   0,
        })
        
    def test_protect_all_false(self):
        t1 = self.create(self.test_model, name="Test 1", protect_all_false='Mr')
        self.assertTagModel(self.test_model.protect_all_false, {
            'Mr':   1,
        })
        
        t1.protect_all_false = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_all_false, {})
    
    def test_case_sensitive_true(self):
        self.assertTagModel(self.test_model.case_sensitive_true, {
            'Mr':   0,
        })
        t1 = self.create(self.test_model, name="Test 1", case_sensitive_true='mr')
        self.assertTagModel(self.test_model.case_sensitive_true, {
            'Mr':   0,
            'mr':   1,
        })
        
    def test_case_sensitive_false(self):
        self.assertTagModel(self.test_model.case_sensitive_false, {
            'Mr':   0,
        })
        t1 = self.create(self.test_model, name="Test 1", case_sensitive_false='mr')
        self.assertTagModel(self.test_model.case_sensitive_false, {
            'Mr':   1,
        })
    
    def test_force_lowercase_true(self):
        t1 = self.create(self.test_model, name="Test 1", force_lowercase_true='Mr')
        self.assertTagModel(self.test_model.force_lowercase_true, {
            'mr':   1,
        })
        
    def test_force_lowercase_false(self):
        t1 = self.create(self.test_model, name="Test 1", force_lowercase_false='Mr')
        self.assertTagModel(self.test_model.force_lowercase_false, {
            'Mr':   1,
        })
