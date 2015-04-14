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


class FormTest(TestCase, TagTestManager):
    def setUp(self):
        # Load initial tags for all models which have them
        tag_models.initial.model_initialise_tags(test_models.SingleFormTest)

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
        tag1_field = test_models.SingleFormTest._meta.get_field('tag1').formfield()
        tag2_field = test_models.SingleFormTest._meta.get_field('tag2').formfield()
        tag3_field = test_models.SingleFormTest._meta.get_field('tag3').formfield()
        self.assertTrue(isinstance(tag1_field, tag_forms.SingleTagField))
        self.assertTrue(isinstance(tag2_field, tag_forms.SingleTagField))
        self.assertTrue(isinstance(tag3_field, tag_forms.SingleTagField))
        
        # Check field options
        self.assertTrue(isinstance(tag1_field.tag_options, tag_models.TagOptions))
        self.assertTrue(isinstance(tag2_field.tag_options, tag_models.TagOptions))
        self.assertTrue(isinstance(tag3_field.tag_options, tag_models.TagOptions))
        self.assertEqual(tag1_field.tag_options.case_sensitive, True)
        self.assertEqual(tag2_field.tag_options.force_lowercase, True)
        self.assertEqual(tag3_field.tag_options.case_sensitive, False)
        self.assertEqual(tag3_field.tag_options.force_lowercase, False)
    
    def test_form_field_output(self):
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
        
    def test_single_model_form(self):
        """
        Test that a model form with a SingleTagField functions correctly
        """
        # Check that the form is created correctly
        form = test_forms.SingleFormTest()
        
        # Check the form media
        media = form.media
        for js in tag_settings.AUTOCOMPLETE_JS:
            self.assertTrue(js in media._js)
        for grp, files in tag_settings.AUTOCOMPLETE_CSS.items():
            self.assertTrue(grp in media._css)
            for css in files:
                self.assertTrue(css in media._css[grp])
        
        # ++
        

# ++ Re-use SingleTagFieldOptionsModel to check data is passed through
# ++ Perhaps ditch current form test models and switch to *OptionsModel?
# ++ Set options in model field, access in form field
# ++ Override options in formfield()
# ++ Set options in form field
