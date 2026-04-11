"""
Tagulous test: Bulk Operations

Tests for the bulk tagging optimisation functionality.
"""

import warnings

from django.test import TestCase

from tests.lib import TagTestManager
from tests.tagulous_tests_app import models as test_models


class BulkOperationsTest(TagTestManager, TestCase):
    """
    Test bulk operations for TagField
    """

    manage_models = [test_models.TagFieldModel]

    def setUpExtra(self):
        self.test_model = test_models.TagFieldModel
        self.tag_model = test_models.TagFieldModel.tags.tag_model

    def test_bulk_add_tag_to_instances_basic(self):
        """Test basic bulk add functionality"""
        instances = [self.create(self.test_model, name=f"Test {i}") for i in range(5)]

        created_count = instances[0].tags.bulk_add_tag_to_instances(
            tag_name="bulk-test",
            instances=instances,
        )

        self.assertEqual(created_count, 5)

        for instance in instances:
            instance.refresh_from_db()
            self.assertIn("bulk-test", [tag.name for tag in instance.tags.all()])

        tag = self.tag_model.objects.get(name="bulk-test")
        self.assertEqual(tag.count, 5)

    def test_bulk_add_tag_to_instances_with_existing(self):
        """Test bulk add when some instances already have the tag"""
        instances = [self.create(self.test_model, name=f"Test {i}") for i in range(5)]

        instances[0].tags.add("bulk-test")
        instances[1].tags.add("bulk-test")

        created_count = instances[0].tags.bulk_add_tag_to_instances(
            tag_name="bulk-test",
            instances=instances,
        )

        self.assertEqual(created_count, 3)

        for instance in instances:
            instance.refresh_from_db()
            self.assertIn("bulk-test", [tag.name for tag in instance.tags.all()])

        tag = self.tag_model.objects.get(name="bulk-test")
        self.assertEqual(tag.count, 5)

    def test_bulk_add_tag_to_instances_empty_list(self):
        """Test bulk add with empty instance list"""
        instance = self.create(self.test_model, name="Test")
        created_count = instance.tags.bulk_add_tag_to_instances(
            tag_name="bulk-test",
            instances=[],
        )

        self.assertEqual(created_count, 0)
        self.assertEqual(self.tag_model.objects.filter(name="bulk-test").count(), 0)

    def test_bulk_add_tag_to_instances_with_queryset(self):
        """Test bulk add with QuerySet of instances"""
        instances = [self.create(self.test_model, name=f"Test {i}") for i in range(5)]

        queryset = self.test_model.objects.all()
        created_count = instances[0].tags.bulk_add_tag_to_instances(
            tag_name="bulk-test",
            instances=queryset,
        )

        self.assertEqual(created_count, 5)

        for instance in instances:
            instance.refresh_from_db()
            self.assertIn("bulk-test", [tag.name for tag in instance.tags.all()])

    def test_bulk_add_tag_to_instances_batching(self):
        """Test bulk add with batching"""
        instances = [self.create(self.test_model, name=f"Test {i}") for i in range(25)]

        created_count = instances[0].tags.bulk_add_tag_to_instances(
            tag_name="bulk-test",
            instances=instances,
            batch_size=10,
        )

        self.assertEqual(created_count, 25)

        for instance in instances:
            instance.refresh_from_db()
            self.assertIn("bulk-test", [tag.name for tag in instance.tags.all()])

        tag = self.tag_model.objects.get(name="bulk-test")
        self.assertEqual(tag.count, 25)

    def test_bulk_add_tag_to_instances_case_insensitive(self):
        """Test bulk add matches existing tags case-insensitively"""
        instances = [self.create(self.test_model, name=f"Test {i}") for i in range(3)]

        instances[0].tags.add("Bulk-Test")

        created_count = instances[0].tags.bulk_add_tag_to_instances(
            tag_name="bulk-test",
            instances=instances,
        )

        self.assertEqual(created_count, 2)
        self.assertEqual(self.tag_model.objects.count(), 1)

        tag = self.tag_model.objects.first()
        self.assertEqual(tag.count, 3)

    def test_bulk_add_warns_when_max_count_set(self):
        """Test that a warning is issued when the field has max_count set"""
        manage_models = [test_models.TagFieldOptionsModel]
        from django_tagulous import models as tag_models

        tag_models.initial.model_initialise_tags(test_models.TagFieldOptionsModel)

        instance = test_models.TagFieldOptionsModel.objects.create(name="Test")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            instance.max_count.bulk_add_tag_to_instances(
                tag_name="x",
                instances=[instance],
            )

        self.assertEqual(len(caught), 1)
        self.assertIn("max_count", str(caught[0].message))


class BulkOperationsQueryCountTest(TagTestManager, TestCase):
    """
    Verify that bulk_add_tag_to_instances uses fewer queries than a naive loop.

    Loop query breakdown (N=5 instances, new tag):
      Instance 1 (creates tag): reload + get-or-create-miss + 2×SAVEPOINT + INSERT tag
                                 + 2×RELEASE + INSERT-OR-IGNORE + UPDATE count = 9
      Instances 2–5 (tag exists): refresh_from_db + reload + get-or-create-hit
                                  + INSERT-OR-IGNORE + UPDATE count = 5 each
      Total: 9 + 5×4 = 29... plus 1 final refresh_from_db = 30

    Bulk query breakdown (any N in one batch, new tag):
      SELECT get-or-create-miss + 2×SAVEPOINT + INSERT tag + 2×RELEASE
      + SAVEPOINT + SELECT existing + INSERT-OR-IGNORE + RELEASE + UPDATE count = 11
    """

    manage_models = [test_models.TagFieldModel]

    def setUpExtra(self):
        self.test_model = test_models.TagFieldModel

    def test_bulk_add_uses_fewer_queries_than_loop(self):
        """Bulk add uses a fixed 11 queries vs 30 for a 5-instance loop"""
        loop_instances = [
            self.create(self.test_model, name="Loop %d" % i) for i in range(5)
        ]
        bulk_instances = [
            self.create(self.test_model, name="Bulk %d" % i) for i in range(5)
        ]

        with self.assertNumQueries(30):
            for inst in loop_instances:
                inst.tags.add("loop-tag")

        with self.assertNumQueries(11):
            bulk_instances[0].tags.bulk_add_tag_to_instances("bulk-tag", bulk_instances)
