"""
Tagulous test: Form TagField

Modules tested:
    tagulous.models.fields.TagField
    tagulous.forms.TagField
"""

import django
from django import forms
from django.test import TestCase

from tagulous import forms as tag_forms
from tagulous import models as tag_models
from tagulous import settings as tag_settings
from tests.lib import TagTestManager, skip_if_mysql, tagfield_html
from tests.tagulous_tests_app import forms as test_forms
from tests.tagulous_tests_app import models as test_models

# ##############################################################################
# ###### Test form TagField
# ##############################################################################


class FormTagFieldTest(TagTestManager, TestCase):
    """
    Test form TagFields
    """

    def test_required(self):
        "Test required status is passed from field to widget"
        self.assertTrue(tag_forms.TagField(required=True).required)
        self.assertTrue(tag_forms.TagField(required=True).widget.is_required)
        self.assertFalse(tag_forms.TagField(required=False).required)
        self.assertFalse(tag_forms.TagField(required=False).widget.is_required)
        self.assertTrue(tag_forms.TagField().required)
        self.assertTrue(tag_forms.TagField().widget.is_required)

    def test_input(self):
        "Test valid and invalid input"
        self.assertFieldOutput(
            tag_forms.TagField,
            valid={
                "red": ["red"],
                "Red, Blue": ["Blue", "Red"],
                '"red, blue", yellow': ["red, blue", "yellow"],
            },
            invalid={},
            empty_value=[],
        )

    def test_force_lowercase(self):
        "Test force_lowercase flag set in constructor"
        self.assertFieldOutput(
            tag_forms.TagField,
            field_kwargs={"tag_options": tag_models.TagOptions(force_lowercase=True)},
            valid={
                "red": ["red"],
                "Red, Blue": ["blue", "red"],
                '"Red, Blue", Yellow': ["red, blue", "yellow"],
            },
            invalid={},
            empty_value=[],
        )

    def test_response(self):
        "Test response is as expected"
        form = test_forms.TagFieldForm(data={"tags": "red, blue"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["tags"], ["blue", "red"])

    def test_render_basics(self):
        "Check widget renders default settings (not required)"

        class LocalTestForm(forms.Form):
            tag = tag_forms.TagField()

        form = LocalTestForm()
        self.assertHTMLEqual(
            str(form["tag"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'id="id_tag" name="tag" {{required}}type="text" />'
            ),
        )

    def test_render_tag_optional(self):
        "Check widget renders correctly when field not required"

        class LocalTestForm(forms.Form):
            tag = tag_forms.TagField(required=False)

        form = LocalTestForm()
        self.assertHTMLEqual(
            str(form["tag"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: false}" '
                'data-tagulous="true" '
                'id="id_tag" name="tag" type="text" />'
            ),
        )

    def test_render_tag_list(self):
        "Check widget renders data-tag-list"

        class LocalTestForm(forms.Form):
            tag = tag_forms.TagField(autocomplete_tags=["one", "two", "three"])

        form = LocalTestForm()
        self.assertHTMLEqual(
            str(form["tag"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'data-tag-list="'
                '[&quot;one&quot;, &quot;two&quot;, &quot;three&quot;]" '
                'id="id_tag" name="tag" {{required}}type="text" />'
            ),
        )

    def test_render_tag_url(self):
        "Check widget renders data-tag-url"
        autocomplete_view = "tagulous_tests_app-unlimited"

        class LocalTestForm(forms.Form):
            tag = tag_forms.TagField(
                tag_options=tag_models.TagOptions(autocomplete_view=autocomplete_view)
            )

        form = LocalTestForm()
        self.assertHTMLEqual(
            str(form["tag"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'data-tag-url="'
                '/tagulous_tests_app/autocomplete/unlimited/" '
                'id="id_tag" name="tag" {{required}}type="text" />'
            ),
        )

    def test_render_value(self):
        "Check widget renders value"
        form = test_forms.TagFieldForm(data={"tags": "run, walk"})
        self.assertHTMLEqual(
            str(form["tags"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'id="id_tags" name="tags" {{required}}type="text" '
                'value="run, walk" />'
            ),
        )

    def test_render_invalid_tag_url(self):
        "Check widget renders data-tag-url"
        autocomplete_view = "tagulous_tests_app-view_does_not_exist"

        class LocalTestForm(forms.Form):
            tag = tag_forms.TagField(
                tag_options=tag_models.TagOptions(autocomplete_view=autocomplete_view)
            )

        form = LocalTestForm()
        with self.assertRaises(ValueError) as cm:
            str(form["tag"])
        self.assertTrue(
            str(cm.exception).startswith(
                "Invalid autocomplete view: Reverse for '{0}' not found. "
                "'{0}' is not a valid view function or pattern name.".format(
                    autocomplete_view
                )
            )
        )

    def test_render_autocomplete_settings(self):
        "Check widget merges autocomplete settings with defaults"

        # Make a form with some autocomplete settings
        class LocalTestForm(forms.Form):
            tags = tag_forms.TagField(
                tag_options=tag_models.TagOptions(
                    autocomplete_settings={"cats": "purr", "cows": "moo"}
                )
            )

        form = LocalTestForm()

        # Set some defaults in the widget
        self.assertEqual(form["tags"].field.widget.default_autocomplete_settings, None)
        form["tags"].field.widget.default_autocomplete_settings = {
            "bees": "buzz",
            "cats": "mew",
        }

        # Render
        # Expecting bees:buzz, cats:purr, cows:moo
        # Order depends on Django version
        expected = (
            '<input autocomplete="off" '
            'data-tag-options="{'
            "&quot;autocomplete_settings&quot;: {SETTINGS}, &quot;required&quot;: true"
            '}"data-tagulous="true" '
            'id="id_tags" name="tags" required type="text" />'
        )
        if django.VERSION < (5, 0):
            expected = expected.replace(
                "SETTINGS",
                (
                    "&quot;cows&quot;: &quot;moo&quot;, "
                    "&quot;bees&quot;: &quot;buzz&quot;, "
                    "&quot;cats&quot;: &quot;purr&quot;"
                ),
            )
        else:
            expected = expected.replace(
                "SETTINGS",
                (
                    "&quot;bees&quot;: &quot;buzz&quot;, "
                    "&quot;cats&quot;: &quot;purr&quot;, "
                    "&quot;cows&quot;: &quot;moo&quot;"
                ),
            )

        self.assertHTMLEqual(str(form["tags"]), expected)

    def test_invalid_prepare_value(self):
        "Check form field raises exception when given an invalid value"
        form = test_forms.TagFieldForm()
        with self.assertRaises(ValueError) as cm:
            form["tags"].field.prepare_value([1, 2])
        self.assertEqual(
            str(cm.exception), "Tag field could not prepare unexpected value"
        )


# ##############################################################################
# ###### Test ModelForm TagField
# ##############################################################################


class ModelFormTagFieldTest(TagTestManager, TestCase):
    """
    Test form TagFields
    """

    manage_models = [test_models.TagFieldModel]

    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.form = test_forms.TagFieldModelForm
        self.model = test_models.TagFieldModel
        self.tag_model = self.model.tags.tag_model

    def test_formfield(self):
        "Test that model.TagField.formfield works correctly"
        # Check that the model fields are generated correctly
        tag1_field = self.model._meta.get_field("tags").formfield()
        self.assertIsInstance(tag1_field, tag_forms.TagField)
        self.assertIsInstance(tag1_field.tag_options, tag_models.TagOptions)

        # Check we can get it from the descriptor shortcut method
        tag2_field = self.model.tags.formfield()
        self.assertIsInstance(tag2_field, tag_forms.TagField)
        self.assertIsInstance(tag2_field.tag_options, tag_models.TagOptions)

    def test_media(self):
        "Test that a model form with a TagField has the correct media"
        media = self.form().media
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
        form = test_forms.TagFieldModelForm(
            data={"name": "Test 1", "tags": "blue, red"}
        )
        self.assertTrue(form.is_valid())
        t1 = form.save()

        # Check in-memory instance
        self.assertEqual(t1.name, "Test 1")
        self.assertEqual(t1.tags, "blue, red")

        # Check database
        self.assertInstanceEqual(t1, name="Test 1", tags="blue, red")
        self.assertTagModel(self.tag_model, {"blue": 1, "red": 1})

    def test_model_form_save_commit_false(self):
        """
        Test that a model form with a TagField saves correctly when
        commit=False
        """
        form = test_forms.TagFieldModelForm(
            data={"name": "Test 1", "tags": "blue, red"}
        )
        self.assertTrue(form.is_valid())
        t1 = form.save(commit=False)
        t1.save()

        # Check in-memory instance
        self.assertEqual(t1.name, "Test 1")
        self.assertEqual(t1.tags, "")
        self.assertTagModel(self.tag_model, {})
        self.assertInstanceEqual(t1, name="Test 1", tags="")

        # Save M2M data
        form.save_m2m()

        # Check in-memory instance
        self.assertEqual(t1.name, "Test 1")
        self.assertEqual(t1.tags, "blue, red")

        # Check database
        self.assertInstanceEqual(t1, name="Test 1", tags="blue, red")
        self.assertTagModel(self.tag_model, {"blue": 1, "red": 1})

    def test_override_option_dict_formfield(self):
        "Test defaults can be overriden in formfield() call with a dict"
        # Confirm default
        field1 = self.form().fields["tags"]
        self.assertEqual(field1.tag_options.case_sensitive, False)

        # Change default
        field2 = self.model.tags.formfield(tag_options={"case_sensitive": True})
        self.assertEqual(field2.tag_options.case_sensitive, True)

    def test_override_option_cls_formfield(self):
        "Test defaults can be overriden in formfield() call with a TagOption"
        # Confirm default
        field1 = self.form().fields["tags"]
        self.assertEqual(field1.tag_options.case_sensitive, False)

        # Change default
        field2 = self.model.tags.formfield(
            tag_options=tag_models.TagOptions(case_sensitive=True)
        )
        self.assertEqual(field2.tag_options.case_sensitive, True)

    def test_override_autocomplete_tags_formfield(self):
        "Test list of autocomplete tags can be passed in formfield"
        self.tag_model.objects.create(name="red")
        self.tag_model.objects.create(name="blue")
        self.tag_model.objects.create(name="green")

        # Confirm default
        field1 = self.form().fields["tags"]
        self.assertSequenceEqual(
            [t.name for t in field1.autocomplete_tags],
            [t.name for t in self.tag_model.objects.all()],
        )

        # Change default
        field2 = self.model.tags.formfield(autocomplete_tags=["pink", "lime"])
        self.assertSequenceEqual(field2.autocomplete_tags, ["pink", "lime"])

    def test_render_tag_list(self):
        "Check widget renders data-tag-list"
        self.tag_model.objects.create(name="red")
        self.tag_model.objects.create(name="blue")
        self.tag_model.objects.create(name="yellow")
        self.assertTagModel(self.tag_model, {"red": 0, "blue": 0, "yellow": 0})
        form = self.form(data={"name": "Test 1", "tags": "red, blue"})
        print(str(form["tags"]))
        self.assertHTMLEqual(
            str(form["tags"]),
            tagfield_html(
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'data-tag-list="'
                '[&quot;blue&quot;, &quot;red&quot;, &quot;yellow&quot;]" '
                'id="id_tags" name="tags" {{required}}type="text" '
                'value="red, blue" />'
            ),
        )

    def test_initial_string(self):
        "Check initial tag string"
        form = test_forms.TagFieldForm(initial={"tags": "red, blue"})
        self.assertHTMLEqual(
            str(form["tags"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'id="id_tags" name="tags" {{required}}type="text" '
                'value="red, blue" />'
            ),
        )

    def test_initial_tag_list(self):
        "Check initial tag list"
        t1 = self.tag_model.objects.create(name="red")
        t2 = self.tag_model.objects.create(name="blue")
        form = test_forms.TagFieldForm(initial={"tags": [t1, t2]})
        self.assertHTMLEqual(
            str(form["tags"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'id="id_tags" name="tags" {{required}}type="text" '
                'value="blue, red" />'
            ),
        )

    def test_initial_tag_queryset(self):
        "Check initial tag queryset"
        self.tag_model.objects.create(name="red")
        self.tag_model.objects.create(name="blue")
        tags = self.tag_model.objects.all()
        form = test_forms.TagFieldForm(initial={"tags": tags})
        self.assertHTMLEqual(
            str(form["tags"]),
            (
                '<input autocomplete="off" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'id="id_tags" name="tags" {{required}}type="text" '
                'value="blue, red" />'
            ),
        )

    def test_tagged_edit(self):
        "Check edit tagged model form instance works"
        t1 = self.model.objects.create(name="Test 1", tags="blue, red")

        form = self.form(instance=t1)

        self.assertHTMLEqual(
            str(form["tags"]),
            tagfield_html(
                '<input autocomplete="off" '
                'data-tag-list="[&quot;blue&quot;, &quot;red&quot;]" '
                'data-tag-options="{&quot;required&quot;: true}" '
                'data-tagulous="true" '
                'id="id_tags" name="tags" {{required}}type="text" '
                'value="blue, red" />'
            ),
        )

    def test_tagmeta_without_autocomplete_settings(self):
        """
        Check that a tag widget copes with a tag field which takes its options
        from a TagModel with a TagMeta, but where the TagMeta is missing
        autocomplete_settings, and the widget has default_autocomplete_settings.
        """

        class TagMetaUserForm(forms.ModelForm):
            class Meta:
                model = test_models.TagMetaUser
                exclude = []

        form = TagMetaUserForm()
        form["two"].field.widget.default_autocomplete_settings = {"bees": "buzz"}

        self.assertHTMLEqual(
            str(form["two"]),
            tagfield_html(
                '<input autocomplete="off" '
                'data-tag-list="[]" '
                'data-tag-options="{&quot;autocomplete_settings&quot;: '
                "{&quot;bees&quot;: &quot;buzz&quot;}, "
                "&quot;case_sensitive&quot;: true, "
                "&quot;force_lowercase&quot;: true, &quot;max_count&quot;: 10, "
                '&quot;required&quot;: false}" '
                'data-tagulous="true" '
                'id="id_two" name="two" type="text" />'
            ),
        )


# ##############################################################################
# ######  Test TagField blank
# ##############################################################################


class ModelFormTagFieldOptionalTest(TagTestManager, TestCase):
    "Test optional TagField"

    manage_models = [test_models.TagFieldOptionalModel]

    def setUpExtra(self):
        self.form = test_forms.TagFieldOptionalModelForm
        self.model = test_models.TagFieldOptionalModel
        self.tag_model = self.model.tag.tag_model

    def test_optional_tagfield(self):
        "Check model with optional tagfield can be saved when empty"
        form = self.form(data={"name": "Test 1"})
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertEqual(t1.name, "Test 1")
        self.assertEqual(t1.tag.count(), 0)
        self.assertTagModel(self.tag_model, {})


class ModelFormTagFieldRequiredTest(TagTestManager, TestCase):
    "Test required TagField"

    manage_models = [test_models.TagFieldRequiredModel]

    def setUpExtra(self):
        self.form = test_forms.TagFieldRequiredModelForm
        self.model = test_models.TagFieldRequiredModel
        self.tag_model = self.model.tag.tag_model

    def test_required_tagfield_set(self):
        "Check model with required tagfield can be saved when set"
        form = self.form(data={"name": "Test 1", "tag": "red, blue"})
        self.assertTrue(form.is_valid())
        t1 = form.save()
        self.assertEqual(t1.name, "Test 1")
        self.assertEqual(t1.tag, "blue, red")
        self.assertEqual(str(t1.tag), "blue, red")
        self.assertIsInstance(t1.tag, tag_models.TagRelatedManagerMixin)
        self.assertEqual(t1.tag.count(), 2)
        self.assertEqual(t1.tag.all()[0], "blue")
        self.assertEqual(t1.tag.all()[1], "red")
        self.assertTagModel(self.tag_model, {"red": 1, "blue": 1})

    def test_required_tagfield_empty(self):
        "Check model with required tagfield cannot be saved when empty"
        form = self.form(data={"name": "Test 1"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors.keys()), 1)
        self.assertEqual(list(form.errors.keys())[0], "tag")
        self.assertEqual(len(form.errors["tag"]), 1)
        self.assertEqual(form.errors["tag"][0], "This field is required.")


# ##############################################################################
# ###### Test form TagField options
# ##############################################################################


class ModelFormTagFieldOptionsTest(TagTestManager, TestCase):
    manage_models = [test_models.TagFieldOptionsModel]

    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.form = test_forms.TagFieldOptionsModelForm
        self.model = test_models.TagFieldOptionsModel

    @skip_if_mysql
    def test_case_sensitive_true(self):
        "Test form TagField case_sensitive true"
        # Prep tag model
        tag_model = self.model.case_sensitive_true.tag_model
        self.assertTagModel(tag_model, {"Adam": 0})

        # Check that the option is passed to the form field from model field
        form = self.form(data={"case_sensitive_true": "adam"})
        field = form.fields["case_sensitive_true"]
        self.assertIsInstance(field, tag_forms.TagField)
        self.assertEqual(field.tag_options.case_sensitive, True)

        # Check that the option is passed to the widget
        self.assertEqual(field.widget.tag_options.case_sensitive, True)

        # No effect on form data
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["case_sensitive_true"], ["adam"])

        # No effect on save
        obj = form.save()
        self.assertEqual(obj.case_sensitive_true, "adam")
        self.assertTagModel(tag_model, {"Adam": 0, "adam": 1})

    @skip_if_mysql
    def test_case_sensitive_false(self):
        "Test form TagField case_sensitive false"
        # Prep tag model
        tag_model = self.model.case_sensitive_false.tag_model

        # Check that the option is passed to the form field from model field
        form = self.form(data={"case_sensitive_false": "adam"})
        field = form.fields["case_sensitive_false"]
        self.assertIsInstance(field, tag_forms.TagField)
        self.assertEqual(field.tag_options.case_sensitive, False)
        self.assertEqual(field.widget.tag_options.case_sensitive, False)

        # Still no effect on form data
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["case_sensitive_false"], ["adam"])

        # But when saved, the instance will be capitalised
        obj = form.save()
        self.assertEqual(obj.case_sensitive_false, "Adam")
        self.assertTagModel(tag_model, {"Adam": 1})

    def test_force_lowercase_true(self):
        "Test form TagField force_lowercase true"
        # Prep tag model
        tag_model = self.model.force_lowercase_true.tag_model

        # Check that the option is passed to the form field from model field
        form = self.form(data={"force_lowercase_true": "Adam"})
        field = form.fields["force_lowercase_true"]
        self.assertIsInstance(field, tag_forms.TagField)
        self.assertEqual(field.tag_options.force_lowercase, True)
        self.assertEqual(field.widget.tag_options.force_lowercase, True)

        # Form data returns lowercase case
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["force_lowercase_true"], ["adam"])

        # When saved, the instance will be lowercase
        obj = form.save()
        self.assertEqual(obj.force_lowercase_true, "adam")
        self.assertTagModel(tag_model, {"adam": 1})

    def test_force_lowercase_false(self):
        "Test form TagField force_lowercase false"
        # Check that the option is passed to the form field from model field
        form = self.form(data={"force_lowercase_false": "Adam"})
        field = form.fields["force_lowercase_false"]
        self.assertIsInstance(field, tag_forms.TagField)
        self.assertEqual(field.tag_options.force_lowercase, False)
        self.assertEqual(field.widget.tag_options.force_lowercase, False)

        # Check the input string is returned in the new case
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["force_lowercase_false"], ["Adam"])

    def test_max_count(self):
        "Test form TagField max_count is passed and enforced"
        # It's not relevant
        # Check that the option is passed to the form field from model field
        form = self.form(data={"max_count": "one"})
        field = form.fields["max_count"]
        self.assertIsInstance(field, tag_forms.TagField)
        self.assertEqual(field.tag_options.max_count, 3)

        # Check the input string is returned in the new case
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["max_count"], ["one"])

        # Check two
        form = self.form(data={"max_count": "one, two"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["max_count"], ["one", "two"])

        # Check three
        form = self.form(data={"max_count": "one, two, three"})
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["max_count"], sorted(["one", "two", "three"])
        )

        # Check four
        form = self.form(data={"max_count": "one, two, three, four"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors.keys()), 1)
        self.assertEqual(list(form.errors.keys())[0], "max_count")
        self.assertEqual(len(form.errors["max_count"]), 1)
        self.assertEqual(
            form.errors["max_count"][0], "This field can only have 3 arguments"
        )

    def text_max_count_1(self):
        "Test form TagField max_count of 1"

        # Mostly just to test grammar of the error message
        class LocalTestForm(forms.Form):
            tags = tag_forms.TagField(tag_options=tag_models.TagOptions(max_count=1))

        form = self.form(data={"max_count": "one"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["max_count"], ["one"])

        # Check two
        form = self.form(data={"max_count": "one, two"})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors.keys()), 1)
        self.assertEqual(list(form.errors.keys())[0], "max_count")
        self.assertEqual(len(form.errors["max_count"]), 1)
        self.assertEqual(
            form.errors["max_count"][0], "This field can only have 1 argument"
        )

    def test_initial_without_autocomplete_initial(self):
        "Check a field with initial but without autocomplete_initial lists all"
        tag_model = self.model.initial_string.tag_model
        tag_model.objects.create(name="David")
        tag_model.objects.create(name="Eric")
        tag_model.objects.create(name="Frank")

        # Confirm default
        field = self.form().fields["initial_string"]
        self.assertSequenceEqual(
            [t.name for t in field.autocomplete_tags],
            [t.name for t in tag_model.objects.all()],
        )

    def test_initial_with_autocomplete_initial(self):
        "Check a field with initial and autocomplete_initial lists initial"
        tag_model = self.model.initial_list.tag_model
        tag_model.objects.create(name="David")
        tag_model.objects.create(name="Eric")
        tag_model.objects.create(name="Frank")

        # Confirm default
        field = self.form().fields["initial_list"]
        self.assertSequenceEqual(
            [t.name for t in field.autocomplete_tags],
            [t.name for t in tag_model.objects.initial()],
        )
