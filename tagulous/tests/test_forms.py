"""
Tagulous test: Forms

Modules tested:
    tagulous.models.managers.BaseTagManager
    tagulous.models.managers.SingleTagManager
    tagulous.models.descriptors.BaseTagDescriptor
    tagulous.models.descriptors.SingleTagDescriptor
    tagulous.models.fields.SingleTagField
    tagulous.models.fields.SingleTagField
"""
from tagulous.tests.lib import *


###############################################################################
####### Test form SingleTagFields
###############################################################################

class FormSingleTagFieldTest(TagTestManager, TestCase):
    """
    Test form SingleTagFields
    """
    manage_models = [
        test_models.SingleTagFieldModel,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.model = test_models.SingleTagFieldModel
        self.tag_model = self.model.title.tag_model
        
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
        tag1_field = self.model._meta.get_field('title').formfield()
        self.assertTrue(isinstance(tag1_field, tag_forms.SingleTagField))
        self.assertTrue(isinstance(tag1_field.tag_options, tag_models.TagOptions))
        
        # Check we can get it from the descriptor shortcut method
        tag2_field = self.model.title.formfield()
        self.assertTrue(isinstance(tag2_field, tag_forms.SingleTagField))
        self.assertTrue(isinstance(tag2_field.tag_options, tag_models.TagOptions))
        
        
    def test_single_model_form(self):
        """
        Test that a model form with a SingleTagField functions correctly
        """
        # Check that the form is created correctly
        form = test_forms.SingleTagFieldForm()
        
        # Check the form media
        media = form.media
        for js in tag_settings.AUTOCOMPLETE_JS:
            self.assertTrue(js in media._js)
        for grp, files in tag_settings.AUTOCOMPLETE_CSS.items():
            self.assertTrue(grp in media._css)
            for css in files:
                self.assertTrue(css in media._css[grp])
        
    def test_single_model_form_save(self):
        """
        Test that a model form with a SingleTagField saves correctly
        """
        form = test_forms.SingleTagFieldForm(
            data={
                'name': 'Test 1',
                'title': 'Mr',
            }
        )
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertTrue(t1.name, 'Test 1')
        self.assertTrue(t1.title, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })


###############################################################################
####### Test form SingleTagField options
###############################################################################

class SingleTagFieldOptionsFormTest(TagTestManager, TestCase):
    manage_models = [
        test_models.SingleTagFieldOptionsModel,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.model = test_models.SingleTagFieldOptionsModel
        
    def test_form_field_output(self):
        """
        Test form field valid and invalid input
        """
        # ++ Replace this with the *FieldOptionsModels
        # Check field output
        self.assertFieldOutput(
            tag_forms.SingleTagField,
            valid={
                'Mr': 'Mr',
                'Mr, Mrs': 'Mr, Mrs',
            },
            invalid={
                '"': [u'This field cannot contain the " character'],
            },
            empty_value=None
        )
        self.assertFieldOutput(
            tag_forms.SingleTagField,
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
    
    @unittest.skip('Test not implemented')
    def test_case_sensitive_true(self):
        # Check that the option is passed to the form field from model field
        # Check that the option can be overridden in formfield() call
        # Check that the option can be set directly in constructor
        # Check that the option is passed to the widget
        pass
    
    @unittest.skip('Test not implemented')
    def test_case_sensitive_false(self):
        pass
    @unittest.skip('Test not implemented')
    def test_force_lowercase_true(self):
        # Check that the option is passed to the form field
        # Check that the option is passed to the widget
        # Check that input string is returned in lower case
        pass
    
    @unittest.skip('Test not implemented')
    def test_force_lowercase_false(self):
        # Check that the option is passed to the form field
        # Check that the option is passed to the widget
        # Check that input string is returned in input case
        pass
    
    @unittest.skip('Test not implemented')
    def test_max_count(self):
        # Check it isn't passed
        pass
    
    @unittest.skip('Test not implemented')
    def test_autocomplete_limit(self):
        # Check it is passed
        pass
    
    @unittest.skip('Test not implemented')
    def test_autocomplete_settings(self):
        # Check settings are passed
        pass


###############################################################################
####### Test form TagFields
###############################################################################

class FormSingleTagFieldTest(TagTestManager, TestCase):
    """
    Test form TagFields
    """
    manage_models = [
        test_models.TagFieldModel,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.model = test_models.TagFieldModel
        self.tag_model = self.model.tags.tag_model
        
    def test_form_field(self):
        """
        Test the form field basics
        """
        self.assertTrue(tag_forms.TagField(required=True).required)
        self.assertTrue(tag_forms.TagField(required=True).widget.is_required)
        self.assertFalse(tag_forms.TagField(required=False).required)
        self.assertFalse(tag_forms.TagField(required=False).widget.is_required)
        self.assertTrue(tag_forms.TagField().required)
        self.assertTrue(tag_forms.TagField().widget.is_required)

    def test_model_formfield(self):
        """
        Test that model.TagField.formfield works correctly
        """
        # Check that the model fields are generated correctly
        tag1_field = self.model._meta.get_field('tags').formfield()
        self.assertTrue(isinstance(tag1_field, tag_forms.TagField))
        self.assertTrue(isinstance(tag1_field.tag_options, tag_models.TagOptions))
        
        # Check we can get it from the descriptor shortcut method
        tag2_field = self.model.tags.formfield()
        self.assertTrue(isinstance(tag2_field, tag_forms.TagField))
        self.assertTrue(isinstance(tag2_field.tag_options, tag_models.TagOptions))
        
        
    def test_model_form(self):
        """
        Test that a model form with a TagField functions correctly
        """
        # Check that the form is created correctly
        form = test_forms.TagFieldForm()
        
        # Check the form media
        media = form.media
        for js in tag_settings.AUTOCOMPLETE_JS:
            self.assertTrue(js in media._js)
        for grp, files in tag_settings.AUTOCOMPLETE_CSS.items():
            self.assertTrue(grp in media._css)
            for css in files:
                self.assertTrue(css in media._css[grp])
        
    def test_model_form_save(self):
        """
        Test that a model form with a TagField saves correctly
        """
        form = test_forms.TagFieldForm(
            data={
                'name': 'Test 1',
                'tags': 'blue, red',
            }
        )
        self.assertTrue(form.is_valid())
        t1 = form.save()
        
        # Check in-memory instance
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.tags, 'blue, red')
        
        # Check database
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue': 1,
            'red': 1,
        })
        
    def test_model_form_save_commit_false(self):
        """
        Test that a model form with a TagField saves correctly when
        commit=False
        """
        form = test_forms.TagFieldForm(
            data={
                'name': 'Test 1',
                'tags': 'blue, red',
            }
        )
        self.assertTrue(form.is_valid())
        t1 = form.save(commit=False)
        t1.save()
        
        # Check in-memory instance
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.tags, '')
        self.assertTagModel(self.tag_model, {})
        self.assertInstanceEqual(t1, name='Test 1', tags='')
        
        # Save M2M data
        form.save_m2m()
        
        # Check in-memory instance
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.tags, 'blue, red')
        
        # Check database
        self.assertInstanceEqual(t1, name='Test 1', tags='blue, red')
        self.assertTagModel(self.tag_model, {
            'blue': 1,
            'red': 1,
        })



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
        form = test_forms.MixedNonTagRefForm(
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
        form = test_forms.MixedNonTagRefForm(
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
