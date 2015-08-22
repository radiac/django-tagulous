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


###############################################################################
####### Test inline formsets
###############################################################################

class SingleInlineFormsetTest(TagTestManager, TestCase):
    """
    Test inline formset for SingleTagField relationships
    """
    manage_models = [
        test_models.SimpleMixedTest,
    ]
    
    def setUpExtra(self):
        self.model = test_models.SimpleMixedTest
        self.tag_model = self.model.singletag.tag_model
        self.formset = test_forms.SimpleMixedSingleInline
    
    def test_add(self):
        tag1 = self.tag_model.objects.create(name='Mr')
        self.assertTagModel(self.tag_model, {'Mr': 0})
        self.assertEqual(self.model.objects.count(), 0)
        
        formset = self.formset(
            data={
                'formset-TOTAL_FORMS': '3',
                'formset-INITIAL_FORMS': '0',
                'formset-MAX_NUM_FORMS': '1000',
                
                'formset-0-name': 'Test 1',
                'formset-0-DELETE': '',
                
                'formset-1-name': 'Test 2',
                'formset-1-DELETE': '',
            },
            instance=tag1,
            prefix='formset'
        )
        self.assertTrue(formset.is_valid())
        formset.save()
        
        self.assertEqual(self.model.objects.count(), 2)
        obj1 = self.model.objects.get(name='Test 1')
        obj2 = self.model.objects.get(name='Test 2')
        self.assertEqual(obj1.singletag, tag1)
        self.assertEqual(obj2.singletag, tag1)
        self.assertTagModel(self.tag_model, {'Mr': 2})
    
    def test_edit_pk(self):
        "Check that edit formset forms refer to the tag pk, not its name"
        obj1 = self.model.objects.create(name='Test 1', singletag='Mr')
        obj2 = self.model.objects.create(name='Test 2', singletag='Mr')
        tag1 = obj1.singletag
        self.assertTagModel(self.tag_model, {'Mr': 2})
        self.assertEqual(self.model.objects.count(), 2)
        
        formset = self.formset(prefix='formset', instance=tag1)
        self.assertHTMLEqual(str(formset.forms[0]['singletag']), (
            '<input type="hidden" name="formset-0-singletag" '
            'value="%d" id="id_formset-0-singletag" />'
        ) % tag1.pk)
        
    
    def test_edit(self):
        obj1 = self.model.objects.create(name='Test 1', singletag='Mr')
        obj2 = self.model.objects.create(name='Test 2', singletag='Mr')
        tag1 = obj1.singletag
        self.assertTagModel(self.tag_model, {'Mr': 2})
        self.assertEqual(self.model.objects.count(), 2)
        
        formset = self.formset(
            data={
                'formset-TOTAL_FORMS': '5',
                'formset-INITIAL_FORMS': '2',
                'formset-MAX_NUM_FORMS': '1000',
                
                'formset-0-name': 'Test 1e',
                'formset-0-id': '%d' % obj1.pk,
                'formset-0-singletag': '%d' % tag1.pk,
                'formset-0-DELETE': '',
                
                'formset-1-name': 'Test 2e',
                'formset-1-id': '%d' % obj2.pk,
                'formset-1-singletag': '%d' % tag1.pk,
                'formset-1-DELETE': '',
            },
            instance=tag1,
            prefix='formset'
        )
        formset.is_valid()
        self.assertTrue(formset.is_valid())
        formset.save()
        
        self.assertEqual(self.model.objects.count(), 2)
        obj1 = self.model.objects.get(name='Test 1e')
        obj2 = self.model.objects.get(name='Test 2e')
        self.assertEqual(obj1.singletag, tag1)
        self.assertEqual(obj2.singletag, tag1)
        self.assertTagModel(self.tag_model, {'Mr': 2})
