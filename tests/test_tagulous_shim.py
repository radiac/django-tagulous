"""
Tagulous test: the tagulous backwards-compatibility shim
"""

import sys
from unittest import mock

from django.apps import apps as django_apps
from django.test import SimpleTestCase


class TagulousShimTest(SimpleTestCase):
    def _clear_module(self, name):
        return sys.modules.pop(name, None)

    def setUp(self):
        affected = [
            name
            for name in list(sys.modules)
            if name == "tagulous"
            or name.startswith("tagulous.")
            or name == "django_tagulous.models"
            or name.startswith("django_tagulous.models.")
            or name == "django_tagulous.forms"
            or name == "django_tagulous.admin"
            or name == "django_tagulous.signals.pre"
        ]
        self._saved_modules = {name: sys.modules[name] for name in affected}
        for name in affected:
            del sys.modules[name]
        self._saved_meta_path = list(sys.meta_path)

    def tearDown(self):
        sys.meta_path[:] = self._saved_meta_path
        for name in list(sys.modules):
            if name == "tagulous" or name.startswith("tagulous."):
                del sys.modules[name]
        sys.modules.update(self._saved_modules)

    def test_import_does_not_require_app_registry_to_be_ready(self):
        with mock.patch.object(django_apps, "apps_ready", False):
            import tagulous  # noqa: F401

    def test_submodule_import_resolves_to_django_tagulous(self):
        import django_tagulous.models
        import tagulous.models

        self.assertIs(tagulous.models, django_tagulous.models)

    def test_nested_submodule_import_resolves_to_django_tagulous(self):
        from django_tagulous.models.fields import TagField
        from tagulous.models.fields import TagField as ShimTagField

        self.assertIs(ShimTagField, TagField)
