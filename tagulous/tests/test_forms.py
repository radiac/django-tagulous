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
        
        # Check field options exists
        self.assertTrue(isinstance(tag1_field.tag_options, tag_models.TagOptions))
        
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
        
    @unittest.skip('Need to change')
    def test_form_field_output(self):
        # ++ Replace this with the *FieldOptionsModels
        # Check field output
        self.assertFieldOutput(
            tag_forms.SingleTagFieldOptionsForm,
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
            tag_forms.SingleTagFieldOptionsForm,
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
        
# ++ Set options in model field, access in form field
# ++ Override options in formfield()
# ++ Set options in form field



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
        
        # Check field options exists
        self.assertTrue(isinstance(tag1_field.tag_options, tag_models.TagOptions))
        
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
        Test that a model form with a SingleTagField saves correctly
        """
        form = test_forms.TagFieldForm(
            data={
                'name': 'Test 1',
                'tags': 'blue, red',
            }
        )
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertTrue(t1.name, 'Test 1')
        self.assertTrue(t1.tags, 'blue, red')
        self.assertTagModel(self.tag_model, {
            'blue': 1,
            'red': 1,
        })
