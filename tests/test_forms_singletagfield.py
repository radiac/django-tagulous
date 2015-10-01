"""
Tagulous test: Form SingleTagField

Modules tested:
    tagulous.models.fields.SingleTagField
    tagulous.forms.SingleTagField
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from django import forms
from django.utils import six

from tests.lib import *


###############################################################################
####### Test form SingleTagField
###############################################################################

class FormSingleTagFieldTest(TagTestManager, TestCase):
    """
    Test form SingleTagFields being used directly (without ModelForm)
    """
    def test_required(self):
        "Test required status is passed from field to widget"
        self.assertTrue(tag_forms.SingleTagField(required=True).required)
        self.assertTrue(tag_forms.SingleTagField(required=True).widget.is_required)
        self.assertFalse(tag_forms.SingleTagField(required=False).required)
        self.assertFalse(tag_forms.SingleTagField(required=False).widget.is_required)
        self.assertTrue(tag_forms.SingleTagField().required)
        self.assertTrue(tag_forms.SingleTagField().widget.is_required)
    
    def test_input(self):
        "Test valid and invalid input"
        self.assertFieldOutput(
            tag_forms.SingleTagField,
            valid={
                'Mr': 'Mr',
                'Mr, Mrs': 'Mr, Mrs',
            },
            invalid={},
            empty_value=None
        )
    
    def test_force_lowercase(self):
        "Test force_lowercase flag set in constructor"
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
            invalid={},
            empty_value=None
        )
    
    def test_response(self):
        "Test response is as expected"
        form = test_forms.SingleTagFieldForm(data={'singletag': 'Mr'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['singletag'], 'Mr')
    
    def test_render_basics(self):
        "Check widget renders default settings (not required)"
        class LocalTestForm(forms.Form):
            tag = tag_forms.SingleTagField()
        form = LocalTestForm()
        self.assertHTMLEqual(six.text_type(form['tag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: true, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'id="id_tag" name="tag" type="text" />'
        ))
        
    def test_render_tag_optional(self):
        "Check widget renders correctly when field not required"
        class LocalTestForm(forms.Form):
            tag = tag_forms.SingleTagField(required=False)
        form = LocalTestForm()
        self.assertHTMLEqual(six.text_type(form['tag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: false, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'id="id_tag" name="tag" type="text" />'
        ))
    
    def test_render_tag_list(self):
        "Check widget renders data-tag-list"
        class LocalTestForm(forms.Form):
            tag = tag_forms.SingleTagField(
                autocomplete_tags=['one', 'two', 'three'],
            )
        form = LocalTestForm()
        self.assertHTMLEqual(six.text_type(form['tag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: true, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'data-tag-list="'
            '[&quot;one&quot;, &quot;two&quot;, &quot;three&quot;]" '
            'id="id_tag" name="tag" type="text" />'
        ))
    
    def test_render_tag_url(self):
        "Check widget renders data-tag-url"
        autocomplete_view = 'tagulous_tests_app-null'
        class LocalTestForm(forms.Form):
            tag = tag_forms.SingleTagField(
                tag_options=tag_models.TagOptions(
                    autocomplete_view=autocomplete_view,
                ),
            )
        form = LocalTestForm()
        self.assertHTMLEqual(six.text_type(form['tag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: true, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'data-tag-url="'
            '/tagulous_tests_app/views/" '
            'id="id_tag" name="tag" type="text" />'
        ))
    
    def test_render_value(self):
        "Check widget renders value"
        form = test_forms.SingleTagFieldForm(data={'singletag': 'Mr'})
        self.assertHTMLEqual(six.text_type(form['singletag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: true, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'id="id_singletag" name="singletag" type="text" '
            'value="Mr" />'
        ))
    

###############################################################################
####### Test ModelForm SingleTagField
###############################################################################

class ModelFormSingleTagFieldTest(TagTestManager, TestCase):
    """
    Test modelform SingleTagFields
    """
    manage_models = [
        test_models.SingleTagFieldModel,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.form = test_forms.SingleTagFieldModelForm
        self.model = test_models.SingleTagFieldModel
        self.tag_model = self.model.title.tag_model
        
    def test_formfield(self):
        "Test that model.SingleTagField.formfield works correctly"
        # Check that the model fields are generated correctly
        tag1_field = self.model._meta.get_field('title').formfield()
        self.assertIsInstance(tag1_field, tag_forms.SingleTagField)
        self.assertIsInstance(tag1_field.tag_options, tag_models.TagOptions)
        
        # Check we can get it from the descriptor shortcut method
        tag2_field = self.model.title.formfield()
        self.assertIsInstance(tag2_field, tag_forms.SingleTagField)
        self.assertIsInstance(tag2_field.tag_options, tag_models.TagOptions)
    
    def test_media(self):
        "Test that a model form with a SingleTagField has the correct media"
        media = self.form().media
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
        form = self.form(data={'name': 'Test 1', 'title': 'Mr'})
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.title, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })

    def test_override_option_dict_formfield(self):
        "Test defaults can be overriden in formfield() call with a dict"
        # Confirm default
        field1 = self.form().fields['title']
        self.assertEqual(field1.tag_options.case_sensitive, False)
        
        # Change default
        field2 = self.model.title.formfield(
            tag_options={'case_sensitive': True}
        )
        self.assertEqual(field2.tag_options.case_sensitive, True)

    def test_override_option_cls_formfield(self):
        "Test defaults can be overriden in formfield() call with a TagOption"
        # Confirm default
        field1 = self.form().fields['title']
        self.assertEqual(field1.tag_options.case_sensitive, False)
        
        # Change default
        field2 = self.model.title.formfield(
            tag_options=tag_models.TagOptions(case_sensitive=True)
        )
        self.assertEqual(field2.tag_options.case_sensitive, True)
        
    def test_override_autocomplete_tags_formfield(self):
        "Test list of autocomplete tags can be passed in formfield"
        self.tag_model.objects.create(name='Mr')
        self.tag_model.objects.create(name='Mrs')
        
        # Confirm default
        field1 = self.form().fields['title']
        self.assertSequenceEqual(
            [t.name for t in field1.autocomplete_tags],
            [t.name for t in self.tag_model.objects.all()],
        )
        
        # Change default
        field2 = self.model.title.formfield(
            autocomplete_tags=['Ms', 'Mx']
        )
        self.assertSequenceEqual(field2.autocomplete_tags, ['Ms', 'Mx'])
        
    def test_render_tag_list(self):
        "Check widget renders data-tag-list"
        self.tag_model.objects.create(name='Mr')
        self.tag_model.objects.create(name='Mrs')
        self.assertTagModel(self.tag_model, {
            'Mr': 0,
            'Mrs': 0,
        })
        form = self.form(data={'name': 'Test 1', 'title': 'Mrs'})
        self.assertHTMLEqual(six.text_type(form['title']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: false, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'data-tag-list="[&quot;Mr&quot;, &quot;Mrs&quot;]" '
            'id="id_title" name="title" type="text" value="Mrs" />'
        ))
    
    def test_initial_string(self):
        "Check initial string"
        form = test_forms.SingleTagFieldForm(initial={'singletag': 'Mr'})
        self.assertHTMLEqual(six.text_type(form['singletag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: true, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'id="id_singletag" name="singletag" type="text" '
            'value="Mr" />'
        ))

    def test_initial_tag(self):
        "Check initial tag"
        t1 = self.tag_model.objects.create(name='Mr')
        form = test_forms.SingleTagFieldForm(initial={'singletag': t1})
        self.assertHTMLEqual(six.text_type(form['singletag']), (
            '<input autocomplete="off" '
            'data-tag-options="{'
            '&quot;required&quot;: true, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'id="id_singletag" name="singletag" type="text" '
            'value="Mr" />'
        ))
    
    def test_tagged_edit(self):
        "Check edit tagged model form instance works"
        t1 = self.model.objects.create(name='Test 1', title='Mr')
        form = self.form(instance=t1)
        self.assertHTMLEqual(six.text_type(form['title']), (
            '<input autocomplete="off" '
            'data-tag-list="[&quot;Mr&quot;]" '
            'data-tag-options="{'
            '&quot;required&quot;: false, &quot;max_count&quot;: 1}" '
            'data-tag-type="single" data-tagulous="true" '
            'id="id_title" name="title" type="text" '
            'value="Mr" />'
        ))
        
    def test_tag_with_delims(self):
        "Check tag with delimiters"
        t1 = self.model.objects.create(name='Test 1', title='One, Two')
        form = self.form(instance=t1, data={'name': t1.name, 'title': t1.title})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['title'], 'One, Two')
        t2 = form.save()
        self.assertEqual(t2.name, 'Test 1')
        self.assertEqual(t2.title, 'One, Two')
        
    def test_tag_with_quotes(self):
        "Check tag with quotes"
        t1 = self.model.objects.create(name='Test 1', title='"One, "Two"')
        form = self.form(instance=t1, data={'name': t1.name, 'title': t1.title})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['title'], '"One, "Two"')
        t2 = form.save()
        self.assertEqual(t2.name, 'Test 1')
        self.assertEqual(t2.title, '"One, "Two"')
        

###############################################################################
#######  Test SingleTagField blank
###############################################################################

class ModelFormSingleTagFieldOptionalTest(TagTestManager, TestCase):
    "Test optional SingleTagField"
    manage_models = [
        test_models.SingleTagFieldOptionalModel,
    ]
    
    def setUpExtra(self):
        self.form = test_forms.SingleTagFieldOptionalModelForm
        self.model = test_models.SingleTagFieldOptionalModel
        self.tag_model = self.model.tag.tag_model
        
    def test_optional_singletagfield(self):
        "Check model with optional singletagfield can be saved when empty"
        form = self.form(data={'name': 'Test 1'})
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.tag, None)
        self.assertTagModel(self.tag_model, {})


class ModelFormSingleTagFieldRequiredTest(TagTestManager, TestCase):
    "Test required SingleTagField"
    manage_models = [
        test_models.SingleTagFieldRequiredModel,
    ]
    
    def setUpExtra(self):
        self.form = test_forms.SingleTagFieldRequiredModelForm
        self.model = test_models.SingleTagFieldRequiredModel
        self.tag_model = self.model.tag.tag_model
    
    def test_required_singletagfield_set(self):
        "Check model with required singletagfield can be saved when set"
        form = self.form(data={'name': 'Test 1', 'tag':  'Mr'})
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertEqual(t1.name, 'Test 1')
        self.assertEqual(t1.tag, 'Mr')
        self.assertTagModel(self.tag_model, {
            'Mr': 1,
        })
    
    def test_required_singletagfield_empty(self):
        "Check model with required singletagfield cannot be saved when empty"
        form = self.form(data={'name': 'Test 1'})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors.keys()), 1)
        self.assertEqual(list(form.errors.keys())[0], 'tag')
        self.assertEqual(len(form.errors['tag']), 1)
        self.assertEqual(form.errors['tag'][0], 'This field is required.')
        

###############################################################################
####### Test form SingleTagField options
###############################################################################

class ModelFormSingleTagFieldOptionsTest(TagTestManager, TestCase):
    "Check tag options"
    manage_models = [
        test_models.SingleTagFieldOptionsModel,
    ]
    
    def setUpExtra(self):
        self.form = test_forms.SingleTagFieldOptionsModelForm
        self.model = test_models.SingleTagFieldOptionsModel
        
    def test_case_sensitive_true(self):
        "Test form SingleTagField case_sensitive true"
        # Prep tag model
        tag_model = self.model.case_sensitive_true.tag_model
        tag_model.objects.get_or_create(name='Mr')
        
        # Check that the option is passed to the form field from model field
        form = self.form(data={'case_sensitive_true': 'mr'})
        field = form.fields['case_sensitive_true']
        self.assertIsInstance(field, tag_forms.SingleTagField)
        self.assertEqual(field.tag_options.case_sensitive, True)
        
        # Check that the option is passed to the widget
        self.assertEqual(field.widget.tag_options.case_sensitive, True)
        
        # No effect on form data
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['case_sensitive_true'], 'mr')
        
        # No effect on save
        obj = form.save()
        self.assertEqual(obj.case_sensitive_true, 'mr')
        self.assertTagModel(tag_model, {
            'Mr': 0,
            'mr': 1,
        })
        
    def test_case_sensitive_false(self):
        "Test form SingleTagField case_sensitive false"
        # Prep tag model
        tag_model = self.model.case_sensitive_false.tag_model
        tag_model.objects.get_or_create(name='Mr')
        
        # Check that the option is passed to the form field from model field
        form = self.form(data={'case_sensitive_false': 'mr'})
        field = form.fields['case_sensitive_false']
        self.assertIsInstance(field, tag_forms.SingleTagField)
        self.assertEqual(field.tag_options.case_sensitive, False)
        self.assertEqual(field.widget.tag_options.case_sensitive, False)
        
        # Still no effect on form data
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['case_sensitive_false'], 'mr')
        
        # But when saved, the instance will be capitalised
        obj = form.save()
        self.assertEqual(obj.case_sensitive_false, 'Mr')
        self.assertTagModel(tag_model, {
            'Mr': 1,
        })
        
    def test_force_lowercase_true(self):
        "Test form SingleTagField force_lowercase true"
        # Prep tag model
        tag_model = self.model.force_lowercase_true.tag_model
        
        # Check that the option is passed to the form field from model field
        form = self.form(data={'force_lowercase_true': 'Mr'})
        field = form.fields['force_lowercase_true']
        self.assertIsInstance(field, tag_forms.SingleTagField)
        self.assertEqual(field.tag_options.force_lowercase, True)
        self.assertEqual(field.widget.tag_options.force_lowercase, True)
        
        # Form data returns lowercase case
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['force_lowercase_true'], 'mr')
        
        # When saved, the instance will be lowercase
        obj = form.save()
        self.assertEqual(obj.force_lowercase_true, 'mr')
        self.assertTagModel(tag_model, {
            'mr': 1,
        })
            
    def test_force_lowercase_false(self):
        "Test form SingleTagField force_lowercase false"
        # Check that the option is passed to the form field from model field
        form = self.form(data={'force_lowercase_false': 'Mr'})
        field = form.fields['force_lowercase_false']
        self.assertIsInstance(field, tag_forms.SingleTagField)
        self.assertEqual(field.tag_options.force_lowercase, False)
        self.assertEqual(field.widget.tag_options.force_lowercase, False)
        
        # Check the input string is returned in the new case
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['force_lowercase_false'], 'Mr')
    
    def test_max_count(self):
        "Test form SingleTagField max_count is 1"
        # It's always 1. Check any field.
        form = self.form()
        field = form.fields['case_sensitive_true']
        self.assertIsInstance(field, tag_forms.SingleTagField)
        self.assertEqual(field.tag_options.max_count, 1)
        self.assertEqual(field.widget.tag_options.max_count, 1)
        
    def test_initial_without_autocomplete_initial(self):
        "Check a field with initial but without autocomplete_initial lists all"
        tag_model = self.model.initial_string.tag_model
        tag_model.objects.create(name='Miss')
        tag_model.objects.create(name='Mx')
        
        # Confirm default
        field = self.form().fields['initial_string']
        self.assertSequenceEqual(
            [t.name for t in field.autocomplete_tags],
            [t.name for t in tag_model.objects.all()],
        )
        
    def test_initial_with_autocomplete_initial(self):
        "Check a field with initial and autocomplete_initial lists initial"
        tag_model = self.model.initial_list.tag_model
        tag_model.objects.create(name='Miss')
        tag_model.objects.create(name='Mx')
        
        # Confirm default
        field = self.form().fields['initial_list']
        self.assertSequenceEqual(
            [t.name for t in field.autocomplete_tags],
            [t.name for t in tag_model.objects.initial()],
        )
