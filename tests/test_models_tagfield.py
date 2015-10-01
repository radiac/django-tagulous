"""
Tagulous test: Model TagField

Modules tested:
    tagulous.models.managers.TagRelatedManager
    tagulous.models.descriptors.BaseTagDescriptor
    tagulous.models.descriptors.TagDescriptor
    tagulous.models.fields.BaseTagField
    tagulous.models.fields.TagField
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from tests.lib import *


class ModelTagFieldTest(TagTestManager, TestCase):
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
        self.assertIsInstance(
            self.tag_field, tag_models.TagDescriptor
        )
    
    def test_tag_table(self):
        "Check the tag table exists"
        if django.VERSION < (1, 9):
            self.assertTrue(issubclass(
                self.tag_field.field.remote_field.to, tag_models.TagModel,
            ))
        else:
            self.assertTrue(issubclass(
                self.tag_field.field.remote_field.model, tag_models.TagModel,
            ))
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
        self.assertEqual(six.text_type(t1.tags), t1.tags.get_tag_string())
        self.assertEqual(len(t1.tags.get_tag_list()), 2)
        self.assertTrue('red' in t1.tags.get_tag_list())
        self.assertTrue('blue' in t1.tags.get_tag_list())
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(six.text_type(t2.tags), '')
        
        # Returned after save
        t1.save()
        t1 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(t1.tags.get_tag_string(), 'blue, red')
        self.assertEqual(six.text_type(t1.tags), t1.tags.get_tag_string())
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
        self.assertEqual(six.text_type(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(six.text_type(t2.tags), '')
        
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
        self.assertEqual(six.text_type(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {})
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(six.text_type(t2.tags), '')
        
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
        self.assertEqual(six.text_type(t1.tags), 'blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      0,
            'blue':     0,
        })
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(six.text_type(t2.tags), '')
        
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
        self.assertEqual(six.text_type(t1.tags), 'blue, red')
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
        self.assertEqual(six.text_type(t1.tags), '')
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
        self.assertEqual(six.text_type(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(six.text_type(t2.tags), 'blue, red')
        
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
        self.assertEqual(six.text_type(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Check db hasn't changed
        t2 = test_models.TagFieldModel.objects.get(name='Test 1')
        self.assertEqual(six.text_type(t2.tags), 'blue, red')
        
        # Returned after save
        t1.tags.save()
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertTagModel(self.tag_model, {})
        
    def test_assign_unknown(self):
        "Check assigning an unknown value raises an exception"
        t1 = self.create(test_models.TagFieldModel, name="Test 1")
        with self.assertRaises(ValueError) as cm:
            # Assign the descriptor to itself, because why not.
            t1.tags = test_models.TagFieldModel.tags
        self.assertEqual(
            six.text_type(cm.exception), 'Unexpected value assigned to TagField'
        )
        
    def test_contains(self):
        "Check __contains__ using strings and Tag objects"
        t1 = self.create(test_models.TagFieldModel, name="1", tags='blue, red')
        
        # String matches
        self.assertTrue('blue' in t1.tags, 'blue not found')
        self.assertTrue('red' in t1.tags, 'red not found')
        
        # Partials shouldn't match
        self.assertFalse('green' in t1.tags, 'green incorrectly found')
        self.assertFalse('blu' in t1.tags, 'blu incorrectly found')
        self.assertFalse('ed' in t1.tags, 'ed incorrectly found')
        
        # Tag objects (will be cast to strings)
        red = t1.tags.tag_model.objects.get(name='red')
        blue = t1.tags.tag_model.objects.get(name='blue')
        green = t1.tags.tag_model.objects.create(name='green')
        self.assertTrue(red in t1.tags, 'red not found')
        self.assertTrue(blue in t1.tags, 'red not found')
        self.assertFalse(green in t1.tags, 'green incorrectly found')
    
    def test_len(self):
        "Check __len__ returns the number of tags"
        t1 = self.create(test_models.TagFieldModel, name="1", tags='blue, red')
        self.assertEqual(len(t1.tags), 2)
    
    def test_eq(self):
        "Check __eq__ correctly determines equality"
        t1 = self.create(test_models.TagFieldModel, name="1", tags='blue, red')
        self.assertEqual(t1.tags, 'blue, red')
        self.assertEqual(t1.tags, 'red, blue')
        self.assertEqual(t1.tags, ['red', 'blue'])
        
        # Test queryset
        tags = t1.tags.tag_model.objects.all()
        self.assertEqual(t1.tags, tags)
        
        # Test another TagRelatedManager
        t2 = self.create(test_models.TagFieldModel, name="2", tags='blue, red')
        self.assertEqual(t1.tags, t2.tags)
    
    def test_ne(self):
        "Check __ne__ correctly determines falsity"
        t1 = self.create(test_models.TagFieldModel, name="1", tags='blue, red')
        self.assertNotEqual(t1.tags, 'red')
        self.assertNotEqual(t1.tags, 'blue')
        self.assertNotEqual(t1.tags, ['red', 'green'])
        self.assertNotEqual(t1.tags, 'green')
        
        # Test another TagRelatedManager
        t2 = self.create(test_models.TagFieldModel, name="2", tags='red, green')
        self.assertNotEqual(t1.tags, t2.tags)
        
        # Test queryset
        tags = t1.tags.tag_model.objects.all()
        self.assertNotEqual(t1.tags, tags)
        
        
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
    
    def test_m2m_set_by_string(self):
        "Set a tag directly using M2M .set(string)"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'red':      1,
        })
        t1.tags.set('green', 'pink')
        self.assertEqual(t1.tags, 'green, pink')
        self.assertInstanceEqual(t1, name='Test 1', tags='green, pink')
        self.assertTagModel(self.tag_model, {
            'green':    1,
            'pink':     1,
        })
        
        # No need to test further arguments, it passes through to add() which
        # is tested thoroughly below

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
    
    def test_m2m_add_by_string_existing(self):
        "Add a tag directly using M2M .add(str) when the tag already exists"
        test_models.TagFieldModel.tags.tag_model.objects.create(name='green')
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue')
        self.assertTagModel(self.tag_model, {
            'blue':     1,
            'green':    0,
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
        
    def test_m2m_remove_missing(self):
        "Remove a tag which doesn't exist (and isn't set)"
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        t1.tags.remove('green')
        self.assertEqual(t1.tags, 'blue, red')
        
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
        self.assertEqual(six.text_type(t1.tags), '')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        self.assertInstanceEqual(t2, name='Test 2', tags='blue, red')
    
    def test_fake_manager_after_delete(self):
        "Check fake manager steps in to store tags when the item is deleted"
        # Create the item
        t1 = self.create(test_models.TagFieldModel, name="Test 1", tags='blue, red')
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'red':      1,
            'blue':     1,
        })
        
        # Now delete it
        t1.delete()
        
        # It won't have a pk any more, but it will have a manager.
        self.assertEqual(t1.pk, None)
        
        # TagDescriptor will now have to create a FakeTagRelatedManager and
        # copy the tags across from the real one. Because although this is
        # about as likely as the previous test, someone will do it eventually.
        manager = t1.tags
        self.assertIsInstance(
            manager, tag_models.managers.FakeTagRelatedManager
        )
        self.assertEqual(manager, 'blue, red')
        
    def test_fake_manager(self):
        "Check that the FakeTagRelatedManager doesn't do databases"
        errmsg = (
            '"<TagFieldModel: TagFieldModel object>" needs to be saved '
            'before TagField can use the database'
        )
        t1 = test_models.TagFieldModel(name="Test 1", tags='blue, red')
        
        with self.assertRaises(ValueError) as cm:
            t1.tags.save()
        self.assertEqual(six.text_type(cm.exception), errmsg)
        
        with self.assertRaises(ValueError) as cm:
            t1.tags.set('fail')
        self.assertEqual(six.text_type(cm.exception), errmsg)
        
        with self.assertRaises(ValueError) as cm:
            t1.tags.add('fail')
        self.assertEqual(six.text_type(cm.exception), errmsg)
        
        with self.assertRaises(ValueError) as cm:
            t1.tags.remove('blue')
        self.assertEqual(six.text_type(cm.exception), errmsg)
        
        with self.assertRaises(ValueError) as cm:
            t1.tags.clear()
        self.assertEqual(six.text_type(cm.exception), errmsg)


###############################################################################
#######  Test invalid fields
###############################################################################

class ModelTagFieldInvalidTest(TagTestManager, TransactionTestCase):
    """
    Test invalid model TagField
    
    Use a TransactionTestCase so the apps will be reset
    """
    manage_models = [
        test_models.SingleTagFieldModel,
    ]
    
    def test_to_model_options_fails(self):
        "Check when a to model is specified, tag options are invalid"
        new_field = tag_models.TagField(
            test_models.TagMetaUser, force_lowercase=True,
        )
        with self.assertRaises(ValueError) as cm:
            new_field._process_deferred_options()
        self.assertEqual(
            six.text_type(cm.exception),
            "Cannot set tag options on explicit tag model "
            "<class 'tests.tagulous_tests_app.models.TagMetaUser'>"
        )
        
    def test_to_model_force_options_works(self):
        "Check when _set_tag_meta is True, options can be set after all"
        self.assertTrue(test_models.TagMetaModel.tag_options.force_lowercase)
        new_field = tag_models.TagField(
            test_models.TagMetaModel, force_lowercase=False,
            _set_tag_meta=True,
        )
        new_field._process_deferred_options()
        self.assertFalse(test_models.TagMetaModel.tag_options.force_lowercase)
        
        # Set force_lowercase back ready for future tests - unittest won't fix
        test_models.TagMetaModel.tag_options.force_lowercase = True
        self.assertTrue(test_models.TagMetaModel.tag_options.force_lowercase)

    def test_contribute_only_once(self):
        "Check that a field can't be contributed more than once"
        field = test_models.TagFieldModel._meta.get_field('tags')
        with self.assertRaises(AttributeError) as cm:
            field.contribute_to_class(test_models.TagFieldModel, 'new_tags')
        self.assertEqual(
            six.text_type(cm.exception),
            "The tag field <tagulous.models.fields.TagField: tags> is already "
            "attached to a model"
        )
    
    def test_invalid_to_model(self):
        "Check that the to model has to be a TagModel subclass"
        with self.assertRaises(ValueError) as cm:
            class FailModel_invalid_to(models.Model):
                to_model = tag_models.TagField(test_models.TagFieldModel)
        self.assertEqual(
            six.text_type(cm.exception),
            "Tag model must be a subclass of TagModel"
        )
        
    def test_forbidden_db_table(self):
        "Check that db_table argument raises exception"
        with self.assertRaises(ValueError) as cm:
            class FailModel_forbidden_db(models.Model):
                db_table = tag_models.TagField(db_table='fail')
        self.assertEqual(
            six.text_type(cm.exception),
            "Invalid argument 'db_table' for TagField"
        )

    def test_forbidden_through(self):
        "Check that through argument raises exception"
        with self.assertRaises(ValueError) as cm:
            class FailModel_forbidden_through(models.Model):
                through = tag_models.TagField(through='fail')
        self.assertEqual(
            six.text_type(cm.exception),
            "Invalid argument 'through' for TagField"
        )

    def test_forbidden_symmetrical(self):
        "Check that symmetrical argument raises exception"
        with self.assertRaises(ValueError) as cm:
            class FailModel_forbidden_symmetrical(models.Model):
                symmetrical = tag_models.TagField(symmetrical='fail')
        self.assertEqual(
            six.text_type(cm.exception),
            "Invalid argument 'symmetrical' for TagField"
        )


###############################################################################
####### Test tag counter
###############################################################################

class ModelTagFieldCountTest(TagTestManager, TestCase):
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
#######  Test model field blank=True
###############################################################################

class ModelTagFieldOptionalTest(TagTestManager, TestCase):
    """
    Test optional TagField
    """
    manage_models = [
        test_models.TagFieldOptionalModel,
    ]
    def test_optional_save_missing(self):
        "Check an optional TagField isn't required for save"
        # If it fails, it will return an exception
        t1 = test_models.TagFieldOptionalModel(name='Test 1')
        t1.save()
        self.assertNotEqual(t1.pk, None)
    
    def test_optional_create_missing(self):
        "Check an optional TagField isn't required for object.create"
        # If it fails, it will return an exception
        t1 = test_models.TagFieldOptionalModel.objects.create(name='Test 1')
        self.assertNotEqual(t1.pk, None)


###############################################################################
####### Test model field blank=False
###############################################################################

class ModelTagFieldRequiredTest(TagTestManager, TestCase):
    """
    Test required model TagField
    """
    manage_models = [
        test_models.TagFieldRequiredModel,
    ]
    def test_required_save(self):
        "Check a required TagField doesn't raise an exception when saved"
        # This isn't exactly the desired action, but as it stands we can't
        # enforce blank=False on a M2M tagfield without rewriting chunks of
        # django's core modelform - it can't even be monkeypatched cleanly.
        # 
        # Future changes to django may make it possible; at that point we can
        # switch this test to enforce blank=False:
        '''
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.TagFieldRequiredModel(name='Test')
            t1.save()
        self.assertEqual(cm.exception.messages[0], 'This field cannot be null.')
        '''
        # but until then:
        t1 = test_models.TagFieldRequiredModel(name='Test')
        t1.save()
        self.assertInstanceEqual(t1, name='Test', tag='')
        
    def test_required_create_raises(self):
        "Check a required TagField raises an exception in object.create"
        # As test_required_save, this isn't desired behaviour, but until django
        # changes, we can't use this test:
        '''
        with self.assertRaises(exceptions.ValidationError) as cm:
            t1 = test_models.TagFieldRequiredModel.objects.create(name='Test')
            t1.full_clean()
        self.assertEqual(cm.exception.messages[0], 'This field cannot be null.')
        '''
        # instead:
        t1 = test_models.TagFieldRequiredModel.objects.create(name='Test')
        self.assertInstanceEqual(t1, name='Test', tag='')
    
    
###############################################################################
####### Test multiple TagFields on a model
###############################################################################

class ModelTagFieldMultipleTest(TagTestManager, TestCase):
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
####### Test TagField with string references to tag model
###############################################################################

class ModelTagFieldStringTest(TagTestManager, TransactionTestCase):
    """
    Test tag field which refers to its tag model with a string
    """
    manage_models = [
        test_models.MixedStringTo,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.MixedStringTo
        self.tag_field = self.test_model.tags
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
        t1 = self.test_model.objects.create(name='Test 1', tags='one, two')
        self.assertTagModel(self.tag_model, {
            'one':  1,
            'two':  1,
        })
        self.assertInstanceEqual(t1, name='Test 1', tags='one, two')
        

class ModelTagFieldSelfTest(TagTestManager, TransactionTestCase):
    """
    Test tag field which refers to itself
    """
    manage_models = [
        test_models.MixedSelfTo,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.MixedSelfTo
        self.tag_field = self.test_model.related
    
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
        t1 = self.test_model.objects.create(name='Test 1', related='one, two')
        self.assertTagModel(self.test_model, {
            'one':  1,
            'two':  1,
            'Test 1': 0,
        })
        self.assertInstanceEqual(t1, name='Test 1', related='one, two')
        


###############################################################################
####### Test TagField options
###############################################################################

class ModelTagFieldOptionsTest(TagTestManager, TransactionTestCase):
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
        
    def test_contains_case_sensitive_true(self):
        "Check case sensitive __contains__"
        t1 = self.create(
            self.test_model, name="Test 1", case_sensitive_true='Django, HTML',
        )
        
        # String matches
        self.assertTrue('Django' in t1.case_sensitive_true)
        self.assertTrue('HTML' in t1.case_sensitive_true)
        
        # Partials and incorrect shouldn't be found
        self.assertFalse('Javascript' in t1.case_sensitive_true)
        self.assertFalse('django' in t1.case_sensitive_true)
        self.assertFalse('Html' in t1.case_sensitive_true)
        
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

    def test_contains_force_lowercase_true(self):
        "Check __contains__ when force lowercase true and case sensitive false"
        t1 = self.create(
            self.test_model, name="Test 1", force_lowercase_true='django, html',
        )
        
        # String matches are forced to lowercase
        self.assertTrue('Django' in t1.force_lowercase_true)
        self.assertTrue('HTML' in t1.force_lowercase_true)
        self.assertTrue('django' in t1.force_lowercase_true)
        self.assertTrue('html' in t1.force_lowercase_true)
        
        # Incorrect shouldn't be found
        self.assertFalse('Javascript' in t1.case_sensitive_true)
        
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
            six.text_type(cm.exception),
            "Cannot set more than 3 tags on this field"
        )
        with self.assertRaises(self.test_model.DoesNotExist) as cm:
            t2 = self.test_model.objects.get(name="Test 1")
        self.assertTagModel(self.test_model.max_count, {})
        
    def test_max_count_assign_above(self):
        t1 = self.create(self.test_model, name="Test 1")
        with self.assertRaises(ValueError) as cm:
            t1.max_count = 'Adam, Brian, Chris, David'
        self.assertEqual(
            six.text_type(cm.exception),
            "Cannot set more than 3 tags on this field"
        )
        self.assertInstanceEqual(t1, name="Test 1", max_count='')
        self.assertTagModel(self.test_model.max_count, {})

    def test_max_count_add_above(self):
        t1 = self.create(self.test_model, name="Test 1", max_count='Adam, Brian')
        with self.assertRaises(ValueError) as cm:
            t1.max_count.add('Chris', 'David')
        self.assertEqual(
            six.text_type(cm.exception),
            "Cannot set more than 3 tags on this field; it already has 2"
        )
        self.assertInstanceEqual(t1, name="Test 1", max_count='Adam, Brian')
        # They won't have been created
        self.assertTagModel(self.test_model.max_count, {
            'Adam':     1,
            'Brian':    1,
        })
