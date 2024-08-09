"""
Tagulous test: Model field order

Modules tested:
    tagulous.models.fields.SingleTagField
    tagulous.models.fields.TagField
"""

from django.test import TestCase

from tests.lib import TagTestManager
from tests.tagulous_tests_app import models as test_models


class ModelFieldOrderTest(TagTestManager, TestCase):
    """
    Test model SingleTagField order
    """

    manage_models = [test_models.MixedOrderTest]

    def test_order_correct(self):
        """
        Check that the order of the non-ManyToMany fields is correct
        This is to check that Django internals haven't changed significantly
        """
        # Check the ordering is as expected
        opts = test_models.MixedOrderTest._meta
        local_fields = sorted(opts.concrete_fields + opts.many_to_many)
        expected_fields = [
            # Auto pk 'id'
            "id",
            # Defined fields
            "char1",
            "fk1",
            "char2",
            "single1",
            "char3",
            "m2m1",
            "char4",
            "multi1",
            "char5",
            "m2m2",
            "char6",
            "fk2",
            "char7",
        ]
        self.assertEqual(len(local_fields), len(expected_fields))
        for i in range(len(local_fields)):
            self.assertEqual(local_fields[i].name, expected_fields[i])
