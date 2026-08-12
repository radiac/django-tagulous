"""
Tagulous test: AppConfig

Modules tested:
    tagulous.apps
"""

from unittest import mock

from django.apps import apps
from django.conf import settings
from django.test import TestCase, override_settings


class RegisterDropulousStaticTest(TestCase):
    """
    Test TagulousConfig._register_dropulous_static()

    django_dropulous is not in this test project's INSTALLED_APPS, so by
    default it needs registering; these tests call it directly rather than via
    ready() (which has already run once for the process by the time tests run).
    """

    def get_config(self):
        return apps.get_app_config("tagulous")

    def test_registers_static_dir_when_dropulous_not_installed(self):
        with override_settings(STATICFILES_DIRS=[]):
            self.get_config()._register_dropulous_static()
            self.assertEqual(len(settings.STATICFILES_DIRS), 1)
            self.assertTrue(
                str(settings.STATICFILES_DIRS[0]).endswith("django_dropulous/static")
            )

    def test_does_not_duplicate_on_repeat_calls(self):
        with override_settings(STATICFILES_DIRS=[]):
            config = self.get_config()
            config._register_dropulous_static()
            config._register_dropulous_static()
            self.assertEqual(len(settings.STATICFILES_DIRS), 1)

    def test_skips_when_dropulous_already_installed(self):
        # Patch the attribute directly rather than using override_settings(),
        # which would trigger Django's real app-registry reload for
        # INSTALLED_APPS changes - overkill for what's just a plain `in` check,
        # and it leaks app-registry state across other tests in the suite
        with (
            mock.patch.object(
                settings,
                "INSTALLED_APPS",
                [*settings.INSTALLED_APPS, "django_dropulous"],
            ),
            override_settings(STATICFILES_DIRS=[]),
        ):
            self.get_config()._register_dropulous_static()
            self.assertEqual(settings.STATICFILES_DIRS, [])
