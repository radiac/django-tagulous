"""
Tagulous test: Model TagField

Modules tested:
    tagulous.models.managers.BaseTagManager
    tagulous.models.managers.SingleTagManager
    tagulous.models.descriptors.BaseTagDescriptor
    tagulous.models.descriptors.SingleTagDescriptor
    tagulous.models.fields.SingleTagField
    tagulous.models.fields.SingleTagField
"""
from tagulous.tests.lib import *


class ModelMultiTagFieldTest(TagTestManager, TestCase):
    """
    Test model TagField
    """
    manage_models = [
        test_models.TagFieldModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.TagFieldModel.tags.tag_model
        self.tag_field = test_models.TagFieldModel.tags
    
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
        t1 = self.create(test_models.TagFieldModel, name="Test")
        self.assertInstanceEqual(t1, name="Test")
        
        # Check the TagDescriptor is returning a TagRelatedManager
        self.assertEqual(t1.tags.__class__.__name__, 'TagRelatedManager')
        
        # Check it also has a reference to the correct model
        self.assertEqual(t1.tags.tag_model, self.tag_model)

    def test_tag_assign_before_save(self):
        """
        Check a tag string can be assigned to an instance which hasn't yet
        been saved
        """
        t1 = test_models.TagFieldModel(name="Test")
        t1.tags = 'blue, red'
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
    def test_tag_assign_in_constructor(self):
        "Check a tag string can be set in the constructor"
        t1 = test_models.TagFieldModel(name="Test", tags='blue, red')
        
        # Returned before save
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Returned after save
        t1.save()
        self.assertInstanceEqual(t1, name='Test', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue': 1,
            'red':  1,
        })
    
    def test_tag_assign_by_list_in_constructor(self):
        "Check a list of strings can be set in the constructor"
        t1 = test_models.TagFieldModel(name="Test", tags=['blue', 'red'])
        
        # Returned before save
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Returned after save
        t1.save()
        self.assertInstanceEqual(t1, name='Test', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':  1,
            'blue': 1,
        })
    
    def test_tag_assign_in_object_create(self):
        "Check a tag string can be set in object.create"
        t1 = test_models.TagFieldModel.objects.create(
            name="Test", tags='blue, red',
        )
        self.assertInstanceEqual(t1, name='Test', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':  1,
            'blue': 1,
        })
        
    def test_tag_assign_by_list_in_object_create(self):
        "Check a list of strings can be set in object.create"
        t1 = test_models.TagFieldModel.objects.create(
            name="Test", tags=['blue', 'red']
        )
        self.assertInstanceEqual(t1, name='Test', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':  1,
            'blue': 1,
        })
        
    def test_tag_assign_by_queryset_in_object_create(self):
        "Check a list of strings can be set in object.create"
        self.tag_model.objects.create(name='blue')
        self.tag_model.objects.create(name='red')
        t1 = test_models.TagFieldModel.objects.create(
            name="Test", tags=self.tag_model.objects.all()
        )
        self.assertInstanceEqual(t1, name='Test', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':  1,
            'blue': 1,
        })
    
    def test_tag_assign_in_object_get_or_create_true(self):
        """
        Check a tag string can be passed in object.get_or_create, when object
        does not exist
        """
        t1, state = test_models.TagFieldModel.objects.get_or_create(
            name='Test', tags='blue, red',
        )
        self.assertEqual(state, True)
        self.assertEqual(t1.name, 'Test')
        self.assertEqual(t1.tags, 'blue, red')
        self.assertTagModel(self.tag_model, {
            'red':  1,
            'blue': 1,
        })
        
    def test_tag_assign_in_object_get_or_create_false(self):
        """
        Check a tag string can be passed in object.get_or_create, when object
        does exist
        """
        t1 = test_models.TagFieldModel.objects.create(
            name="Test", tags='blue, red',
        )
        t2 = test_models.TagFieldModel.objects.create(
            name="Test", tags='green',
        )
        t3, state = test_models.TagFieldModel.objects.get_or_create(
            name='Test', tags='blue, red',
        )
        self.assertEqual(state, False)
        self.assertEqual(t1.pk, t3.pk)
        self.assertInstanceEqual(t2, name="Test", tags='green')
        self.assertEqual(t3.name, 'Test')
        self.assertEqual(t3.tags, 'blue, red')
        self.assertTagModel(self.tag_model, {
            'red':   1,
            'blue':  1,
            'green': 1,
        })
        
    def test_tag_assign_string_obj_save(self):
        """
        Check a tag string can be assigned to the descriptor, saved when the
        instance is saved, and returned
        
        Checks TagRelatedManager post_save listener
        """
        t1 = self.create(test_models.TagFieldModel, name="Test 1")
        t1.tags = 'red, blue'
        
        # Returned before save
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertEqual('%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(u'%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(len(t1.tags.get_tag_list()), 2)
        self.assertTrue('red' in t1.tags.get_tag_list())
        self.assertTrue('blue' in t1.tags.get_tag_list())
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.save()
        t1 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertEqual('%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(u'%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(len(t1.tags.get_tag_list()), 2)
        self.assertTrue('red' in t1.tags.get_tag_list())
        self.assertTrue('blue' in t1.tags.get_tag_list())
        self.assertTagModel(self.tag_model, {
            'red':  1,
            'blue': 1,
        })
        
    def test_tag_assign_string_manager_save(self):
        """
        Check a tag string can be assigned to the descriptor, saved by the tag
        manager, and returned
        
        Checks TagRelatedManager.save
        """
        t1 = self.create(test_models.TagFieldModel, name="Test 1")
        t1.tags = 'red, blue'
        
        # Returned before save
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })

    def test_assign_list_strings(self):
        "Check tags can be set with a list of strings"
        t1 = self.create(test_models.TagFieldModel, name="Test 1")
        t1.tags = ['red', 'blue']
        
        # Returned before save
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    def test_assign_list_objs(self):
        "Check tags can be set with a list of strings"
        t1 = self.create(test_models.TagFieldModel, name="Test 1")
        t1.tags = [
            self.tag_model.objects.create(name='blue'),
            self.tag_model.objects.create(name='red')
        ]
        
        # Returned before save
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      0,
            'blue':     0,
        })
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    def test_assign_queryset(self):
        "Check tags can be set with a queryset of tags"
        t1 = self.create(test_models.TagFieldModel, name="Test 1")
        self.tag_model.objects.create(name='blue')
        self.tag_model.objects.create(name='red')
        t1.tags = self.tag_model.objects.all()
        
        # Returned before save, check DB hasn't changed
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {
            'red':      0,
            'blue':     0,
        })
        
        # Returned after save
        t1.tags.save()
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    def test_tag_assign_string_empty(self):
        "Check setting an empty string clears tags"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        t1.tags = ''
        
        # Returned before save, check DB hasn't changed
        self.assertEqual(str(t1.tags), '')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {})
        
    def test_assign_list_empty(self):
        "Check setting an empty list clears tags"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        t1.tags = []
        
        # Returned before save
        self.assertEqual(str(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), 'blue, red')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {})
        
    def test_assign_none(self):
        "Check setting None clears tags"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        t1.tags = None
        
        # Returned before save
        self.assertEqual(str(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), 'blue, red')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {})
        
    def test_multiple_instances(self):
        "Check multiple tagged instances work without interference"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='green, red')
        t3 = self.create(test_models.TagFieldModel, name="Test 3", tags='blue, green')
        
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertInstanceEqual(t2, name='Test 2', tags='green, red')
        self.assertInstanceEqual(t3, name='Test 3', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'red':      2,
            'blue':     2,
            'green':    2,
        })
        
    def test_change_string_add(self):
        "Add a tag by changing tag string"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags = 'blue, green'
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags.save()
        self.assertEqual(t1.tags, 'blue, green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
    
    def test_m2m_add_by_obj(self):
        "Add a tag directly using M2M .add(obj)"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags.add(
            self.tag_model.objects.create(name='green')
        )
        self.assertEqual(t1.tags, 'blue, green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
        
    def test_m2m_add_by_string(self):
        "Add a tag directly using M2M .add(str)"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags.add('green')
        self.assertEqual(t1.tags, 'blue, green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
    
    def test_change_string_remove(self):
        "Remove a tag by changing tag string"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        
        t1.tags = 'green'
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
            'red':      1,
        })
    
    def test_m2m_remove_by_obj(self):
        "Remove a tag directly using M2M .remove(obj)"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        
        t1.tags.remove(
            self.tag_model.objects.get(name='blue')
        )
        self.assertEqual(t1.tags, 'green')
        self.assertInstanceEqual(t1, name='Test 1', tags='green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
            'red':      1,
        })
        
    def test_m2m_remove_by_str(self):
        "Remove a tag directly using M2M .remove(str)"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        
        t1.tags.remove('blue')
        self.assertEqual(t1.tags, 'green')
        self.assertInstanceEqual(t1, name='Test 1', tags='green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
            'red':      1,
        })
    
    def test_m2m_remove_not_set(self):
        "Remove a tag which exists but isn't set"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        
        t1.tags.remove('blue', 'green', 'red')
        self.assertEqual(t1.tags, '')
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'red':      1,
        })
    
    def test_m2m_clear(self):
        "Clear all tags from an item with manager.clear"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      2,
            'blue':     2,
        })
        
        # Returned before save
        t1.tags.clear()
        self.assertEqual(str(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')

        
###############################################################################
####### Test tag counter
###############################################################################

class ModelMultiTagFieldCountTest(TagTestManager, TestCase):
    """
    Test tag model counter
    """
    manage_models = [
        test_models.TagFieldModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.TagFieldModel.tags.tag_model
        self.tag_field = test_models.TagFieldModel.tags
    
    def test_count_0_create(self):
        "Check an unprotected tag can be created with a tag count of 0"
        self.tag_model.objects.create(name='red')
        self.assertTagModel(self.tag_model, {
            'red':      0,
        })
        
    def test_count_0_delete(self):
        "Check that an unprotected tag is deleted when count changes to 0"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
        
        t1.tags.remove('blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='green')
        self.assertTagModel(self.tag_model, {
            'green':    1,
        })
    
    def test_instance_delete_updates(self):
        "Check that deleting an instance updates the count"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.TagFieldModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        
        t1.delete()
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'red':      1,
        })
    
    def test_protected_remains(self):
        "Check that a protected tag stays when count changes to 0"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
        
        green = self.tag_model.objects.get(name='green')
        green.protected = True
        green.save()
        
        t1.delete()
        self.assertTagModel(self.tag_model, {
            'green':    0,
        })
    
    def test_clear_count_0_delete(self):
        """
        Check that an unprotected tag is deleted when clear changes count to 0,
        but protected tag remains
        """
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
        
        green = self.tag_model.objects.get(name='green')
        green.protected = True
        green.save()
        
        t1.tags.clear()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {
            'green':    0,
        })
        
    
###############################################################################
####### Test multiple TagFields on a model
###############################################################################

class ModelMultiTagFieldMultipleTest(TagTestManager, TestCase):
    """
    Test multiple tag fields on a model
    """
    manage_models = [
        test_models.TagFieldMultipleModel,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.TagFieldMultipleModel
        self.tag_field_1 = test_models.TagFieldMultipleModel.tags1
        self.tag_field_2 = test_models.TagFieldMultipleModel.tags2
        self.tag_field_3 = test_models.TagFieldMultipleModel.tags3
    
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
            '_Tagulous_TagFieldMultipleModel_tags1'
        )
        self.assertEqual(
            self.tag_field_2.tag_model.__name__,
            '_Tagulous_TagFieldMultipleModel_tags2'
        )
        self.assertEqual(
            self.tag_field_3.tag_model.__name__,
            '_Tagulous_TagFieldMultipleModel_tags3'
        )
    
    def test_set_and_get(self):
        "Test multiple fields can be set and retrieved independently"
        t1 = self.create(
            self.test_model, name="Test 1",
            tags1='adam, brian',
            tags2='alice, brenda',
            tags3='aragorn, bilbo',
        )
        t2 = self.create(
            self.test_model, name="Test 2",
            tags1='chris, david',
            tags2='claire, daphne',
            tags3='celeborn, denethor',
        )
        t3 = self.create(
            self.test_model, name="Test 3",
            tags1='eric, frank',
            tags2='edith, faye',
            tags3='eowyn, frodo',
        )
        
        self.assertTagModel(self.tag_field_1, {
            'adam':     1,  'brian':    1,  'chris':    1,
            'david':    1,  'eric':     1,  'frank':    1,
        })
        self.assertTagModel(self.tag_field_2, {
            'alice':    1,  'brenda':   1,  'claire':   1,
            'daphne':   1,  'edith':    1,  'faye':     1,
        })
        self.assertTagModel(self.tag_field_3, {
            'aragorn':  1,  'bilbo':    1,  'celeborn': 1,
            'denethor': 1,  'eowyn':    1,  'frodo':    1,
        })
        
        self.assertInstanceEqual(
            t1, name="Test 1",
            tags1='adam, brian',
            tags2='alice, brenda',
            tags3='aragorn, bilbo',
        )
        self.assertInstanceEqual(
            t2, name="Test 2",
            tags1='chris, david',
            tags2='claire, daphne',
            tags3='celeborn, denethor',
        )
        self.assertInstanceEqual(
            t3, name="Test 3",
            tags1='eric, frank',
            tags2='edith, faye',
            tags3='eowyn, frodo',
        )



###############################################################################
####### Test TagField options
###############################################################################

class ModelTagFieldOptionsTest(TagTestManager, TestCase):
    """
    Test tag field options
    """
    manage_models = [
        test_models.TagFieldOptionsModel,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.TagFieldOptionsModel
    
    def test_initial_string(self):
        # Initial will have been loaded by TagTestManager
        self.assertTagModel(self.test_model.initial_string, {
            'Adam':     0,
            'Brian':    0,
            'Chris':    0,
        })
        
    def test_initial_list(self):
        # Initial will have been loaded by TagTestManager
        self.assertTagModel(self.test_model.initial_list, {
            'Adam':     0,
            'Brian':    0,
            'Chris':    0,
        })
    
    def test_protect_initial_true(self):
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Adam':     0,
        })
        
        t1 = self.create(self.test_model, name="Test 1", protect_initial_true='Adam')
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Adam':     1,
        })
        
        t1.protect_initial_true = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Adam':     0,
        })
        
    def test_protect_initial_false(self):
        self.assertTagModel(self.test_model.protect_initial_true, {
            'Adam':     0,
        })
        
        t1 = self.create(self.test_model, name="Test 1", protect_initial_false='Adam')
        self.assertTagModel(self.test_model.protect_initial_false, {
            'Adam':     1,
        })
        
        t1.protect_initial_false = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_initial_false, {})
    
    def test_protect_all_true(self):
        t1 = self.create(self.test_model, name="Test 1", protect_all_true='Adam')
        self.assertTagModel(self.test_model.protect_all_true, {
            'Adam':     1,
        })
        
        t1.protect_all_true = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_all_true, {
            'Adam':     0,
        })
        
    def test_protect_all_false(self):
        t1 = self.create(self.test_model, name="Test 1", protect_all_false='Adam')
        self.assertTagModel(self.test_model.protect_all_false, {
            'Adam':     1,
        })
        
        t1.protect_all_false = ''
        t1.save()
        self.assertTagModel(self.test_model.protect_all_false, {})
    
    def test_case_sensitive_true(self):
        self.assertTagModel(self.test_model.case_sensitive_true, {
            'Adam':     0,
        })
        t1 = self.create(self.test_model, name="Test 1", case_sensitive_true='adam')
        self.assertTagModel(self.test_model.case_sensitive_true, {
            'Adam':     0,
            'adam':     1,
        })
        
    def test_case_sensitive_false(self):
        self.assertTagModel(self.test_model.case_sensitive_false, {
            'Adam':     0,
        })
        t1 = self.create(self.test_model, name="Test 1", case_sensitive_false='adam')
        self.assertTagModel(self.test_model.case_sensitive_false, {
            'Adam':     1,
        })
    
    def test_cmp_case_sensitive_true(self):
        "Test case sensitive matches"
        t1 = self.create(
            self.test_model, name="Test 1", case_sensitive_true='django, html',
        )
        self.assertEqual(t1.case_sensitive_true, 'django, html')
        self.assertNotEqual(t1.case_sensitive_true, 'django, HTML')
        self.assertNotEqual(t1.case_sensitive_true, 'Django, html')
        
    def test_cmp_case_sensitive_false(self):
        """
        Test case insensitive matches
        
        Note: force_lowercase is also false here
        """
        t1 = self.create(
            self.test_model, name="Test 1", case_sensitive_false='Adam, Brian',
        )
        self.assertEqual(t1.case_sensitive_false, 'Adam, Brian')
        self.assertEqual(t1.case_sensitive_false, 'adam, BRIAN')
        self.assertNotEqual(t1.case_sensitive_false, 'Chris')
        
    def test_force_lowercase_true(self):
        t1 = self.create(self.test_model, name="Test 1", force_lowercase_true='Adam')
        self.assertTagModel(self.test_model.force_lowercase_true, {
            'adam':     1,
        })
        
    def test_force_lowercase_false(self):
        t1 = self.create(self.test_model, name="Test 1", force_lowercase_false='Adam')
        self.assertTagModel(self.test_model.force_lowercase_false, {
            'Adam':     1,
        })
    
    def test_cmp_force_lowercase_true(self):
        "Test matches when force lowercase true and case sensitive is false"
        t1 = self.create(
            self.test_model, name="Test 1", force_lowercase_true='blue, red',
        )
        self.assertEqual(t1.force_lowercase_true, 'blue, red')
        self.assertEqual(t1.force_lowercase_true, 'Blue, RED')
        self.assertNotEqual(t1.force_lowercase_true, 'green')

    def test_cmp_case_sensitive_true_force_lowercase_true(self):
        "Test matches when case sensitive and force lowercase true"
        t1 = self.create(
            self.test_model, name="Test 1",
            case_sensitive_true_force_lowercase_true='blue, red',
        )
        self.assertEqual(t1.case_sensitive_true_force_lowercase_true, 'blue, red')
        self.assertEqual(t1.case_sensitive_true_force_lowercase_true, 'Blue, RED')
        self.assertNotEqual(t1.case_sensitive_true_force_lowercase_true, 'green')

    def test_max_count_below(self):
        t1 = self.create(self.test_model, name="Test 1", max_count='Adam')
        self.assertInstanceEqual(t1, name="Test 1", max_count='Adam')
        self.assertTagModel(self.test_model.max_count, {
            'Adam':     1,
        })

    def test_max_count_equal(self):
        t1 = self.create(self.test_model, name="Test 1", max_count='Adam, Brian, Chris')
        self.assertInstanceEqual(t1, name="Test 1", max_count='Adam, Brian, Chris')
        self.assertTagModel(self.test_model.max_count, {
            'Adam':     1,
            'Brian':    1,
            'Chris':    1,
        })
        
    def test_max_count_create_above(self):
        with self.assertRaises(ValueError) as cm:
            t1 = self.test_model.objects.create(
                name="Test 1",
                max_count='Adam, Brian, Chris, David',
            )
        self.assertEqual(
            str(cm.exception),
            "Cannot set more than 3 tags on this field"
        )
        with self.assertRaises(self.test_model.DoesNotExist) as cm:
            t2 = self.test_model.objects.get(name="Test 1")
        self.assertTagModel(self.test_model.max_count, {})
        
    def test_max_count_assign_above(self):
        t1 = self.create(self.test_model, name="Test 1")
        with self.assertRaises(ValueError) as cm:
            t1.max_count = 'Adam, Brian, Chris, David'
            #t1.max_count.save()
            
        self.assertEqual(
            str(cm.exception),
            "Cannot set more than 3 tags on this field"
        )
        self.assertInstanceEqual(t1, name="Test 1", max_count='')
        self.assertTagModel(self.test_model.max_count, {})

    def test_max_count_add_above(self):
        t1 = self.create(self.test_model, name="Test 1", max_count='Adam, Brian')
        with self.assertRaises(ValueError) as cm:
            t1.max_count.add('Chris', 'David')
        self.assertEqual(
            str(cm.exception),
            "Cannot set more than 3 tags on this field; it already has 2"
        )
        self.assertInstanceEqual(t1, name="Test 1", max_count='Adam, Brian')
        # They'll have been created, but not added
        self.assertTagModel(self.test_model.max_count, {
            'Adam':     1,
            'Brian':    1,
            'Chris':    0,
            'David':    0,
        })
        