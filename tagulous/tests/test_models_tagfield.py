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
        test_models.MultiTestModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.MultiTestModel.tags.tag_model
        self.tag_field = test_models.MultiTestModel.tags
    
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
        t1 = self.create(test_models.MultiTestModel, name="Test")
        self.assertInstanceEqual(t1, name="Test")
        
        # Check the TagDescriptor is returning a TagRelatedManager
        self.assertEqual(t1.tags.__class__.__name__, 'TagRelatedManager')
        
        # Check it also has a reference to the correct model
        self.assertEqual(t1.tags.tag_model, self.tag_model)

    @unittest.skip('not yet implemented: constructor')
    def test_tag_assignment_in_constructor(self):
        "Check a tag string can be set in the constructor"
        t1 = test_models.MultiTestModel(name="Test", tags='red, blue')
        
        # Returned before save
        self.assertEqual(t1.tags.get_tag_string(), 'red, blue')
        self.assertTagModel(self.tag_model, {})
        
        # Returned after save
        t1.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':       1,
            'blue':   1,
        })
    
    @unittest.skip('not yet implemented: cache value, save on obj')
    def test_tag_assign_string_obj_save(self):
        """
        Check a tag string can be assigned to the descriptor, saved when the
        instance is saved, and returned
        
        Checks TagRelatedManager post_save listener
        """
        t1 = self.create(test_models.MultiTestModel, name="Test 1")
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
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.save()
        t1 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertEqual('%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(u'%s' % t1.tags, t1.tags.get_tag_string())
        self.assertEqual(len(t1.tags.get_tag_list()), 2)
        self.assertTrue('red' in t1.tags.get_tag_list())
        self.assertTrue('blue' in t1.tags.get_tag_list())
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_tag_assign_string_manager_save(self):
        """
        Check a tag string can be assigned to the descriptor, saved by the tag
        manager, and returned
        
        Checks TagRelatedManager.save
        """
        t1 = self.create(test_models.MultiTestModel, name="Test 1")
        t1.tags = 'red, blue'
        
        # Returned before save
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })

    @unittest.skip('not yet implemented: cache, manager.save')
    def test_assign_list_strings(self):
        "Check tags can be set with a list of strings"
        t1 = self.create(test_models.MultiTestModel, name="Test 1")
        t1.tags = ['red', 'blue']
        
        # Returned before save
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_assign_list_objs(self):
        "Check tags can be set with a list of strings"
        t1 = self.create(test_models.MultiTestModel, name="Test 1")
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
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_assign_queryset(self):
        "Check tags can be set with a queryset of tags"
        t1 = self.create(test_models.MultiTestModel, name="Test 1")
        self.tag_model.objects.create(name='blue')
        self.tag_model.objects.create(name='red')
        t1.tags = self.tag_model.objects.all()
        
        # Returned before save
        self.assertEqual(str(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      0,
            'blue':     0,
        })
        
        # Check db hasn't changed
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), '')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_tag_assign_string_empty(self):
        "Check setting an empty string clears tags"
        t1 = self.create(test_models.MultiTestModel, name="Test", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        t1.tags = ''
        
        # Returned before save
        self.assertEqual(str(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Check db hasn't changed
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), 'blue, red')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {})
        
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_assign_list_empty(self):
        "Check setting an empty list clears tags"
        t1 = self.create(test_models.MultiTestModel, name="Test", tags='blue, red')
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
        t2 = test_models.MultiTestModel.objects.get(name='Test 1')
        self.assertEqual(str(t2.tags), 'blue, red')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {})
        
    def test_multiple_instances(self):
        "Check multiple tagged instances work without interference"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, red')
        t2 = self.create(test_models.MultiTestModel, name="Test 2", tags='green, red')
        t3 = self.create(test_models.MultiTestModel, name="Test 3", tags='blue, green')
        
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertInstanceEqual(t2, name='Test 2', tags='green, red')
        self.assertInstanceEqual(t3, name='Test 3', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'red':      2,
            'blue':     2,
            'green':    2,
        })
        
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_change_string_add(self):
        "Add a tag by changing tag string"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags = 'blue, green'
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
    
    def test_m2m_add_by_obj(self):
        "Add a tag directly using M2M .add(obj)"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags.add(
            self.tag_model.objects.create(name='green')
        )
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
        
    def test_m2m_add_by_string(self):
        "Add a tag directly using M2M .add(str)"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
        })
        t1.tags.add('green')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
        })
    
    @unittest.skip('not yet implemented: cache, manager.save')
    def test_change_string_remove(self):
        "Remove a tag by changing tag string"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.MultiTestModel, name="Test 2", tags='blue, red')
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
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.MultiTestModel, name="Test 2", tags='blue, red')
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
        self.assertInstanceEqual(t1, name='Test 1', tags='green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
            'red':      1,
        })
        
    def test_m2m_remove_by_str(self):
        "Remove a tag directly using M2M .remove(str)"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.MultiTestModel, name="Test 2", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     2,
            'green':    1,
            'red':      1,
        })
        
        t1.tags.remove('blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='green')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    1,
            'red':      1,
        })
    
    def test_m2m_clear(self):
        "Clear all tags from an item with manager.clear"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, red')
        t2 = self.create(test_models.MultiTestModel, name="Test 2", tags='blue, red')
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
        test_models.MultiTestModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.MultiTestModel.tags.tag_model
        self.tag_field = test_models.MultiTestModel.tags
    
    def test_count_0_create(self):
        "Check an unprotected tag can be created with a tag count of 0"
        self.tag_model.objects.create(name='red')
        self.assertTagModel(self.tag_model, {
            'red':      0,
        })
        
    def test_count_0_delete(self):
        "Check that an unprotected tag is deleted when count changes to 0"
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
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
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
        t2 = self.create(test_models.MultiTestModel, name="Test 2", tags='blue, red')
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
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
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
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
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
####### Test multiple tag fields on a model
###############################################################################

class ModelMultiTagFieldMultipleTest(TagTestManager, TestCase):
    """
    Test multiple tag fields on a model
    """
    manage_models = [
        test_models.MultiTestModel,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.MultiTestModel.tags.tag_model
        self.tag_field = test_models.MultiTestModel.tags
    
    def test_fields_dont_interfere(self):
        t1 = self.create(test_models.MultiTestModel, name="Test 1", tags='blue, green')
        # ++ Not the right model
