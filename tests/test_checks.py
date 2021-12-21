from django.test import TestCase, override_settings

from tagulous.checks import SERIALIZATION_MODULES_EXPECTED, WARNING_W001, tagulous_check


class CheckTest(TestCase):
    @override_settings(SERIALIZATION_MODULES=None)
    def test_serialization_modules_missing__check_raises_warning(self):
        self.assertEqual(WARNING_W001.id, "tagulous.W001")
        expected_errors = [WARNING_W001]
        errors = tagulous_check(app_configs=None)
        self.assertEqual(errors, expected_errors)

    @override_settings(SERIALIZATION_MODULES=SERIALIZATION_MODULES_EXPECTED)
    def test_serialization_modules_set__check_raises_no_warning(self):
        expected_errors = []
        errors = tagulous_check(app_configs=None)
        self.assertEqual(errors, expected_errors)
