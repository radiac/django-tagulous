"""
Tagulous test: Model field order

Modules tested:
    tagulous.models.fields.SingleTagField
    tagulous.models.fields.TagField
"""
from __future__ import absolute_import
from tests.lib import *


class ModelFieldOrderTest(TagTestManager, TestCase):
    """
    Test model SingleTagField order
    """
    manage_models = [
        test_models.MixedOrderTest,
    ]
    
    def test_order_correct(self):
        """
        Check that the order of the non-ManyToMany fields is correct
        This is to check that Django internals haven't changed significantly
        """
        # Check the ordering is as expected
        opts = test_models.MixedOrderTest._meta
        # Django 1.4 and 1.5 don't have concrete_fields in meta Options.
        # Django 1.8 states that it's an internal function and shouldn't be
        # used directly, but using it anyway to keep code simple.
        if hasattr(opts, 'concrete_fields'):
            concrete_fields = opts.concrete_fields
        else:
            concrete_fields = [f for f in opts.fields if f.column is not None]
        local_fields = sorted(concrete_fields + opts.many_to_many)
        expected_fields = [
            # Auto pk 'id'
            'id',
            # Defined fields
            'char1', 'fk1', 'char2', 'single1', 'char3', 'm2m1', 'char4',
            'multi1', 'char5', 'm2m2', 'char6', 'fk2', 'char7',
        ]
        self.assertEqual(len(local_fields), len(expected_fields))
        for i in range(len(local_fields)):
            self.assertEqual(local_fields[i].name, expected_fields[i])
