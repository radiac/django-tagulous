"""
Tagulous test: can_create option for TagField and SingleTagField

Tests the can_create option which restricts tag creation:
    - tagulous.forms.TagFormMixin
    - tagulous.forms.BaseTagField.can_create_error
    - can_create option on TagField and SingleTagField
    - Resolution order: form attr > model instance > model class > field option
"""

from django import forms
from django.test import TestCase

import django_tagulous as tagulous
from django_tagulous import forms as tag_forms
from django_tagulous import models as tag_models
from tests.lib import TagTestManager
from tests.tagulous_tests_app import models as test_models

# ##############################################################################
# ###### TagFormMixin unit tests
# ##############################################################################


class TagFormMixinTest(TestCase):
    """
    Test TagFormMixin constructor kwarg extraction and attribute setting
    """

    def test_constructor_kwargs_extracted(self):
        "can_create_<fieldname> kwargs are popped and set as attributes"

        class LocalForm(forms.Form):
            tags = tag_forms.TagField()

        form = LocalForm(data={"tags": "red"}, can_create_tags=False)
        self.assertFalse(form.can_create_tags)

    def test_multiple_kwargs(self):
        "Multiple can_create_* kwargs are all extracted"

        class LocalForm(forms.Form):
            tags = tag_forms.TagField()
            labels = tag_forms.TagField()

        form = LocalForm(
            data={"tags": "red", "labels": "green"},
            can_create_tags=False,
            can_create_labels=True,
        )
        self.assertFalse(form.can_create_tags)
        self.assertTrue(form.can_create_labels)

    def test_non_tag_kwargs_untouched(self):
        "Non can_create_* kwargs are passed through normally"

        class LocalForm(forms.Form):
            tags = tag_forms.TagField()

        # Would raise TypeError if the kwarg weren't handled
        form = LocalForm(data={"tags": "red"}, can_create_tags=False)
        self.assertIsNotNone(form)

    def test_attribute_set_after_init(self):
        "can_create_* attributes can be set on form after instantiation"

        class LocalForm(forms.Form):
            tags = tag_forms.TagField()

        form = LocalForm(data={"tags": "red"})
        form.can_create_tags = False
        self.assertFalse(form.can_create_tags)


# ##############################################################################
# ###### can_create on TagField
# ##############################################################################


class TagFieldCanCreateTest(TagTestManager, TestCase):
    """
    Test can_create enforcement on TagField
    """

    manage_models = [test_models.TagFieldModel]

    def setUpExtra(self):
        self.tag_model = test_models.TagFieldModel.tags.tag_model
        # Pre-populate one existing tag
        self.tag_model.objects.create(name="existing")

    def _make_form(self, can_create=None, can_create_error=None):
        """Build a plain form with a TagField backed by the tag model queryset"""
        kwargs = {}
        tag_opts = {}
        if can_create is not None:
            tag_opts["can_create"] = can_create
        if can_create_error is not None:
            kwargs["can_create_error"] = can_create_error

        class LocalForm(forms.Form):
            tags = tag_forms.TagField(
                tag_options=tag_models.TagOptions(**tag_opts),
                autocomplete_tags=self.tag_model.objects.all(),
                **kwargs,
            )

        return LocalForm

    # -- Default (can_create=True) ----------------------------------------

    def test_default_allows_new_tags(self):
        "Default can_create=True allows new tags through"
        Form = self._make_form()
        form = Form(data={"tags": "new-tag"})
        self.assertTrue(form.is_valid())

    def test_default_allows_existing_tags(self):
        "Default can_create=True allows existing tags through"
        Form = self._make_form()
        form = Form(data={"tags": "existing"})
        self.assertTrue(form.is_valid())

    # -- Field-level can_create=False ------------------------------------

    def test_field_blocks_new_tags(self):
        "can_create=False on field raises ValidationError for new tags"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "brand-new"})
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)

    def test_field_allows_existing_tags(self):
        "can_create=False on field allows tags that already exist"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "existing"})
        self.assertTrue(form.is_valid())

    def test_field_blocks_mix_of_new_and_existing(self):
        "can_create=False blocks submission if any tag is new"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "existing, brand-new"})
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)

    def test_empty_value_allowed(self):
        "Empty submission is not blocked by can_create=False"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": ""})
        # May be invalid due to required=True, but not a can_create error
        if not form.is_valid():
            self.assertNotIn(
                "cannot_create", [e.code for e in form.errors.as_data().get("tags", [])]
            )

    # -- custom error message --------------------------------------------

    def test_default_error_message(self):
        "Default error message is used when can_create=False"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "brand-new"})
        form.is_valid()
        self.assertIn("cannot_create", [e.code for e in form.errors.as_data()["tags"]])
        self.assertIn("cannot create new tags", form.errors["tags"][0].lower())

    def test_custom_error_message(self):
        "Custom can_create_error message is shown"
        Form = self._make_form(
            can_create=False, can_create_error="No new tags allowed."
        )
        form = Form(data={"tags": "brand-new"})
        form.is_valid()
        self.assertEqual(form.errors["tags"][0], "No new tags allowed.")

    def test_error_code(self):
        "ValidationError has the correct code"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "brand-new"})
        form.is_valid()
        codes = [e.code for e in form.errors.as_data()["tags"]]
        self.assertIn("cannot_create", codes)

    # -- Form attribute override -----------------------------------------

    def test_form_attr_false_overrides_field_true(self):
        "form.can_create_tags=False overrides field can_create=True (default)"
        Form = self._make_form()  # can_create defaults to True
        form = Form(data={"tags": "brand-new"})
        form.can_create_tags = False
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)

    def test_form_attr_true_overrides_field_false(self):
        "form.can_create_tags=True overrides field can_create=False"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "brand-new"})
        form.can_create_tags = True
        self.assertTrue(form.is_valid())

    def test_constructor_kwarg_false_overrides_field_true(self):
        "can_create_tags=False kwarg in constructor overrides field can_create=True"
        Form = self._make_form()
        form = Form(data={"tags": "brand-new"}, can_create_tags=False)
        self.assertFalse(form.is_valid())

    def test_constructor_kwarg_true_overrides_field_false(self):
        "can_create_tags=True kwarg overrides field can_create=False"
        Form = self._make_form(can_create=False)
        form = Form(data={"tags": "brand-new"}, can_create_tags=True)
        self.assertTrue(form.is_valid())


# ##############################################################################
# ###### can_create on TagField ModelForm (resolution chain)
# ##############################################################################


class TagFieldModelFormCanCreateTest(TagTestManager, TestCase):
    """
    Test resolution chain: field option < model class < model instance < form attr
    """

    manage_models = [test_models.TagFieldModel]

    def setUpExtra(self):
        self.tag_model = test_models.TagFieldModel.tags.tag_model
        self.tag_model.objects.create(name="existing")

    def tearDownExtra(self):
        # Clean up any class-level attributes set during tests
        try:
            delattr(test_models.TagFieldModel, "can_create_tags")
        except AttributeError:
            pass

    def _make_model_form(self):
        class LocalForm(forms.ModelForm):
            class Meta:
                model = test_models.TagFieldModel
                fields = ["name", "tags"]

        return LocalForm

    def test_model_form_default_allows_new(self):
        "ModelForm with default can_create=True allows new tags"
        Form = self._make_model_form()
        form = Form(data={"name": "x", "tags": "brand-new"})
        self.assertTrue(form.is_valid())

    def test_model_instance_attr_blocks(self):
        "form.instance.can_create_tags=False blocks new tags"
        Form = self._make_model_form()
        instance = test_models.TagFieldModel(name="x")
        instance.can_create_tags = False
        form = Form(data={"name": "x", "tags": "brand-new"}, instance=instance)
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)

    def test_model_instance_attr_allows_existing(self):
        "form.instance.can_create_tags=False allows existing tags"
        Form = self._make_model_form()
        instance = test_models.TagFieldModel(name="x")
        instance.can_create_tags = False
        form = Form(data={"name": "x", "tags": "existing"}, instance=instance)
        self.assertTrue(form.is_valid())

    def test_model_class_attr_blocks(self):
        "Model class can_create_tags=False blocks new tags for all instances"
        test_models.TagFieldModel.can_create_tags = False
        try:
            Form = self._make_model_form()
            form = Form(data={"name": "x", "tags": "brand-new"})
            self.assertFalse(form.is_valid())
            self.assertIn("tags", form.errors)
        finally:
            del test_models.TagFieldModel.can_create_tags

    def test_form_attr_overrides_model_instance(self):
        "form.can_create_tags=True overrides instance.can_create_tags=False"
        Form = self._make_model_form()
        instance = test_models.TagFieldModel(name="x")
        instance.can_create_tags = False
        form = Form(data={"name": "x", "tags": "brand-new"}, instance=instance)
        form.can_create_tags = True
        self.assertTrue(form.is_valid())

    def test_form_attr_overrides_model_class(self):
        "form.can_create_tags=True overrides class.can_create_tags=False"
        test_models.TagFieldModel.can_create_tags = False
        try:
            Form = self._make_model_form()
            form = Form(data={"name": "x", "tags": "brand-new"})
            form.can_create_tags = True
            self.assertTrue(form.is_valid())
        finally:
            del test_models.TagFieldModel.can_create_tags

    def test_instance_attr_overrides_class_attr(self):
        "instance.can_create_tags=True overrides class.can_create_tags=False"
        test_models.TagFieldModel.can_create_tags = False
        try:
            Form = self._make_model_form()
            instance = test_models.TagFieldModel(name="x")
            instance.can_create_tags = True
            form = Form(data={"name": "x", "tags": "brand-new"}, instance=instance)
            self.assertTrue(form.is_valid())
        finally:
            del test_models.TagFieldModel.can_create_tags


# ##############################################################################
# ###### can_create on SingleTagField
# ##############################################################################


class SingleTagFieldCanCreateTest(TagTestManager, TestCase):
    """
    Test can_create enforcement on SingleTagField
    """

    manage_models = [test_models.SingleTagFieldModel]

    def setUpExtra(self):
        self.tag_model = test_models.SingleTagFieldModel.title.tag_model
        self.tag_model.objects.create(name="Mr")

    def _make_form(self, can_create=None):
        tag_opts = {}
        if can_create is not None:
            tag_opts["can_create"] = can_create

        class LocalForm(forms.Form):
            title = tag_forms.SingleTagField(
                tag_options=tag_models.TagOptions(**tag_opts),
                autocomplete_tags=self.tag_model.objects.all(),
                required=False,
            )

        return LocalForm

    def test_default_allows_new(self):
        "Default can_create=True allows new single tag"
        Form = self._make_form()
        form = Form(data={"title": "Dr"})
        self.assertTrue(form.is_valid())

    def test_field_blocks_new(self):
        "can_create=False on SingleTagField blocks new tags"
        Form = self._make_form(can_create=False)
        form = Form(data={"title": "Dr"})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_field_allows_existing(self):
        "can_create=False on SingleTagField allows existing tags"
        Form = self._make_form(can_create=False)
        form = Form(data={"title": "Mr"})
        self.assertTrue(form.is_valid())

    def test_form_attr_overrides(self):
        "form.can_create_title overrides field option on SingleTagField"
        Form = self._make_form(can_create=False)
        form = Form(data={"title": "Dr"})
        form.can_create_title = True
        self.assertTrue(form.is_valid())


# ##############################################################################
# ###### No autocomplete_tags (fail-safe behaviour)
# ##############################################################################


class CanCreateNoAutocompleteTagsTest(TestCase):
    """
    When autocomplete_tags is not set, can_create=False treats all tags as new
    """

    def test_no_autocomplete_tags_blocks_all(self):
        "Without autocomplete_tags, any tag is treated as new when can_create=False"

        class LocalForm(forms.Form):
            tags = tag_forms.TagField(
                tag_options=tag_models.TagOptions(can_create=False),
                # No autocomplete_tags
            )

        form = LocalForm(data={"tags": "anything"})
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)


# ##############################################################################
# ###### Auto-injection
# ##############################################################################


class AutoInjectionTest(TestCase):
    """
    Test that TagFormMixin is auto-injected into Django's form base classes
    """

    def test_form_has_mixin(self):
        "django.forms.Form has TagFormMixin in its MRO after app ready()"
        self.assertIn(tag_forms.TagFormMixin, forms.Form.__mro__)

    def test_model_form_has_mixin(self):
        "ModelForm has TagFormMixin in its MRO after app ready()"
        self.assertIn(tag_forms.TagFormMixin, forms.ModelForm.__mro__)

    def test_plain_form_accepts_can_create_kwarg(self):
        "A plain django.forms.Form accepts can_create_* kwargs without error"

        class LocalForm(forms.Form):
            name = forms.CharField()

        # Should not raise TypeError
        form = LocalForm(data={"name": "x"}, can_create_foo=False)
        self.assertFalse(form.can_create_foo)
