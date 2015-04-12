"""
Tagulous test: Model SingleTagField

Modules tested:
    tagulous.models.managers.BaseTagManager
    tagulous.models.managers.SingleTagManager
    tagulous.models.descriptors.BaseTagDescriptor
    tagulous.models.descriptors.SingleTagDescriptor
    tagulous.models.fields.BaseTagField
    tagulous.models.fields.SingleTagField
"""
from tagulous.tests.lib import *


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
        t1 = self.create(test_models.SingleTagFieldModel, name="Test")
        self.assertInstanceEqual(t1, name="Test", title=None)
        self.assertTagModel(self.tag_model, {})
    
    def test_tag_assignment(self):
        "Check a tag string can be assigned to descriptor and returned"
        t1 = self.create(test_models.SingleTagFieldModel, name="Test")
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
        "Check a tag string can be set in the constructor"
        t1 = test_models.SingleTagFieldModel(name="Test", title='Mr')
        t1.save()
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_tag_assignment_in_object_create(self):
        "Check a tag string can be passed in object.create"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test', title='Mr')
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_tag_assignment_in_object_get_or_create_true(self):
        """
        Check a tag string can be passed in object.get_or_create, when object
        does not exist
        """
        t1, state = test_models.SingleTagFieldModel.objects.get_or_create(name='Test', title='Mr')
        self.assertEqual(state, True)
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.title.name, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
        
    def test_tag_assignment_in_object_get_or_create_false(self):
        """
        Check a tag string can be passed in object.get_or_create, when object
        does exist
        """
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test', title='Mr')
        t2, state = test_models.SingleTagFieldModel.objects.get_or_create(name='Test', title='Mr')
        self.assertEqual(state, False)
        self.assertEqual(t1.pk, t2.pk)
        self.assertEqual(t1.name, t2.name)
        self.assertEqual(t2.name, 'Test')
        self.assertEqual(t2.title.name, 'Mr')
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
        self.assertEqual(str(t1.title), 'Mr')
        self.assertEqual(str(t2.title), 'Mr')
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
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
        
    def test_assign_by_object_in_object_create(self):
        "Check a tag object can be passed in object.create"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title=t1.title)
        self.assertEqual(t1.title, t2.title)
        self.assertEqual(t1.title.pk, t2.title.pk)
        self.assertTagModel(self.tag_model, {
            'Mr': 2,
        })
    
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
    
    def test_multiple_unsaved(self):
        "Check that there's no leak between unsaved objects"
        t1 = test_models.SingleTagFieldModel(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel(name='Test 1', title='Mrs')
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
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.get(pk=t1.pk)
        self.assertEqual(t1.title, t2.title)
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })


###############################################################################
#######  Test model field blank=True
###############################################################################

class ModelSingleTagFieldOptionalTest(TagTestManager, TestCase):
    """
    Test model SingleTagField
    """
    manage_models = [
        test_models.SingleTagFieldOptionalModel,
    ]
    def test_optional_saves_without_exception(self):
        "Check an optional SingleTagField isn't required for save"
        try:
            t1 = test_models.SingleTagFieldOptionalModel(name='Test 1')
            t1.save()
            t2 = test_models.SingleTagFieldOptionalModel.objects.create(name='Test 1')
        except Exception, e:
            self.fail(
                'Optional SingleTagField raised exception unexpectedly: %s' % e
            )


###############################################################################
####### Test model field blank=False
###############################################################################

class ModelSingleTagFieldRequiredTest(TagTestManager, TestCase):
    """
    Test model SingleTagField
    """
    manage_models = [
        test_models.SingleTagFieldRequiredModel,
    ]
    def test_required_raises_exception_on_save(self):
        "Check a required SingleTagField raises an exception when saved"
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.SingleTagFieldRequiredModel(name='Test')
            t1.save()
        self.assertEqual(cm.exception.messages[0], u'This field cannot be null.')
    
    def test_required_raises_exception_in_object_create(self):
        "Check a required SingleTagField raises an exception in object.create"
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.SingleTagFieldRequiredModel.objects.create(name='Test')
        self.assertEqual(cm.exception.messages[0], u'This field cannot be null.')
    
    
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
        t1 = self.create(self.test_model, name="Test 1", tag1='Mr', tag2='blue', tag3='adam')
        t2 = self.create(self.test_model, name="Test 2", tag1='Mrs', tag2='green', tag3='brian')
        t3 = self.create(self.test_model, name="Test 3", tag1='Ms', tag2='red', tag3='chris')
        
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

# ++ Forgot - queryset needs to support lowercase and case-sensitive options
