"""
Tagulous test: Forms with SingleTagField and TagFields

Modules tested:
    tagulous.models.fields.SingleTagField
    tagulous.models.fields.TagField
    tagulous.forms.SingleTagField
    tagulous.forms.TagField
"""
from __future__ import absolute_import
from tests.lib import *



###############################################################################
####### Test mixed form
###############################################################################

class FormMixedNonTagRefTest(TagTestManager, TestCase):
    """
    Test form TagFields
    """
    manage_models = [
        test_models.MixedNonTagRefTest,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.model = test_models.MixedNonTagRefTest
        self.tag_model = self.model.singletag.tag_model
        
    def test_model_form_save(self):
        """
        Test that a model form with a TagField saves correctly with other
        relationships
        """
        tag1 = self.tag_model.objects.create(name='blue')
        tag2 = self.tag_model.objects.create(name='red')
        tag3 = self.tag_model.objects.create(name='green')
        form = test_forms.MixedNonTagRefModelForm(
            data={
                'name': 'Test 1',
                'singletag': 'purple',
                'tags': 'yellow, orange',
                'fk': tag1.pk,
                'mm': [tag2.pk, tag3.pk],
            }
        )
        self.assertTrue(form.is_valid())
        t1 = form.save()
        
        # Check in-memory instance
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.singletag, 'purple')
        self.assertEqual(t1.tags, 'orange, yellow')
        self.assertEqual(t1.fk, tag1)
        self.assertEqual(list(t1.mm.all().order_by('pk')), [tag2, tag3])
        
        # Check database
        self.assertInstanceEqual(
            t1, name='Test 1', singletag='purple', tags='orange, yellow',
            fk=tag1, mm=[tag2, tag3],
        )
        self.assertTagModel(self.tag_model, {
            'blue': 0,
            'red': 0,
            'green': 0,
            'purple': 1,
            'orange': 1,
            'yellow': 1,
        })
    
    def test_model_form_save_commit_false(self):
        """
        Test that a model form with a TagField saves correctly when save_m2m
        is also called
        """
        tag1 = self.tag_model.objects.create(name='blue')
        tag2 = self.tag_model.objects.create(name='red')
        tag3 = self.tag_model.objects.create(name='green')
        form = test_forms.MixedNonTagRefModelForm(
            data={
                'name': 'Test 1',
                'singletag': 'purple',
                'tags': 'orange, yellow',
                'fk': tag1.pk,
                'mm': [tag2.pk, tag3.pk],
            }
        )
        self.assertTrue(form.is_valid())
        t1 = form.save(commit=False)
        t1.save()
        form.save_m2m()
        
        # Check in-memory instance
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.singletag, 'purple')
        self.assertEqual(t1.tags, 'orange, yellow')
        self.assertEqual(t1.fk, tag1)
        self.assertEqual(list(t1.mm.all().order_by('pk')), [tag2, tag3])
        
        # Check database
        self.assertInstanceEqual(
            t1, name='Test 1', singletag='purple', tags='orange, yellow',
            fk=tag1, mm=[tag2, tag3],
        )
        self.assertTagModel(self.tag_model, {
            'blue': 0,
            'red': 0,
            'green': 0,
            'purple': 1,
            'orange': 1,
            'yellow': 1,
        })
