"""
Tagulous test: Bulk Operations

Tests for the bulk tagging optimization functionality.
"""

from django.db import models, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.test.utils import override_settings

from tagulous import models as tag_models
from tagulous.models.managers import TagRelatedManagerMixin
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
        # Create test instances
        instances = []
        for i in range(5):
            instances.append(self.create(self.test_model, name=f"Test {i}"))

        # Use bulk add
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='bulk-test',
            instances=instances,
            tag_field_name='tags'
        )

        # Should have created 5 relationships
        self.assertEqual(created_count, 5)

        # Check that all instances now have the tag
        for instance in instances:
            instance.refresh_from_db()
            self.assertIn('bulk-test', [tag.name for tag in instance.tags.all()])

        # Check tag count
        tag = self.tag_model.objects.get(name='bulk-test')
        self.assertEqual(tag.count, 5)

    def test_bulk_add_tag_to_instances_with_existing(self):
        """Test bulk add when some instances already have the tag"""
        # Create test instances
        instances = []
        for i in range(5):
            instances.append(self.create(self.test_model, name=f"Test {i}"))

        # Manually add tag to first two instances
        instances[0].tags.add('bulk-test')
        instances[1].tags.add('bulk-test')

        # Use bulk add - should only add to the remaining 3
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='bulk-test',
            instances=instances,
            tag_field_name='tags'
        )

        # Should have created 3 new relationships
        self.assertEqual(created_count, 3)

        # Check that all instances now have the tag
        for instance in instances:
            instance.refresh_from_db()
            self.assertIn('bulk-test', [tag.name for tag in instance.tags.all()])

        # Check tag count (should be 5 total)
        tag = self.tag_model.objects.get(name='bulk-test')
        self.assertEqual(tag.count, 5)

    def test_bulk_add_tag_to_instances_empty_list(self):
        """Test bulk add with empty instance list"""
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='bulk-test',
            instances=[],
            tag_field_name='tags'
        )

        # Should have created 0 relationships
        self.assertEqual(created_count, 0)

        # Tag should not exist
        self.assertEqual(self.tag_model.objects.filter(name='bulk-test').count(), 0)

    def test_bulk_add_tag_to_instances_with_queryset(self):
        """Test bulk add with QuerySet of instances"""
        # Create test instances
        instances = []
        for i in range(5):
            instances.append(self.create(self.test_model, name=f"Test {i}"))

        # Use bulk add with QuerySet
        queryset = self.test_model.objects.all()
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='bulk-test',
            instances=queryset,
            tag_field_name='tags'
        )

        # Should have created 5 relationships
        self.assertEqual(created_count, 5)

        # Check that all instances now have the tag
        for instance in instances:
            instance.refresh_from_db()
            self.assertIn('bulk-test', [tag.name for tag in instance.tags.all()])

    def test_bulk_add_tag_to_instances_batching(self):
        """Test bulk add with batching"""
        # Create many test instances
        instances = []
        for i in range(25):
            instances.append(self.create(self.test_model, name=f"Test {i}"))

        # Use bulk add with small batch size
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='bulk-test',
            instances=instances,
            tag_field_name='tags',
            batch_size=10
        )

        # Should have created 25 relationships
        self.assertEqual(created_count, 25)

        # Check that all instances now have the tag
        for instance in instances:
            instance.refresh_from_db()
            self.assertIn('bulk-test', [tag.name for tag in instance.tags.all()])

        # Check tag count
        tag = self.tag_model.objects.get(name='bulk-test')
        self.assertEqual(tag.count, 25)

    def test_bulk_add_tag_to_instances_case_insensitive(self):
        """Test bulk add with case insensitive tags"""
        # Create test instances
        instances = []
        for i in range(3):
            instances.append(self.create(self.test_model, name=f"Test {i}"))

        # First add a tag with different case
        instances[0].tags.add('Bulk-Test')

        # Use bulk add with lowercase - should match existing tag
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='bulk-test',
            instances=instances,
            tag_field_name='tags'
        )

        # Should have created 2 new relationships (instance 0 already has it)
        self.assertEqual(created_count, 2)

        # Should only have one tag in database (case insensitive match)
        self.assertEqual(self.tag_model.objects.count(), 1)

        # Check tag count
        tag = self.tag_model.objects.first()
        self.assertEqual(tag.count, 3)

    def test_bulk_add_invalid_field_name(self):
        """Test bulk add with invalid field name"""
        instances = [self.create(self.test_model, name="Test")]

        with self.assertRaises(ValueError) as cm:
            TagRelatedManagerMixin.bulk_add_tag_to_instances(
                tag_name='bulk-test',
                instances=[instances[0]],
                tag_field_name='nonexistent_field'
            )

        self.assertIn("does not have field 'nonexistent_field'", str(cm.exception))

    def test_bulk_add_non_tag_field(self):
        """Test bulk add with non-tag field"""
        instances = [self.create(self.test_model, name="Test")]

        with self.assertRaises(ValueError) as cm:
            TagRelatedManagerMixin.bulk_add_tag_to_instances(
                tag_name='bulk-test',
                instances=[instances[0]],
                tag_field_name='name'  # This is a CharField, not TagField
            )

        self.assertIn("is not a TagField", str(cm.exception))

    def test_class_method_direct_usage(self):
        """Test using the class method directly (alternative to utility function)"""
        # Create test instances
        instances = []
        for i in range(3):
            instances.append(self.create(self.test_model, name=f"Test {i}"))

        # Use class method directly
        created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
            tag_name='direct-test',
            instances=instances,
            tag_field_name='tags'
        )

        # Should have created 3 relationships
        self.assertEqual(created_count, 3)

        # Check that all instances now have the tag
        for instance in instances:
            instance.refresh_from_db()
            self.assertIn('direct-test', [tag.name for tag in instance.tags.all()])

class BulkOperationsPerformanceTest(TagTestManager, TestCase):
    """
    Test performance characteristics of bulk operations
    """

    manage_models = [test_models.TagFieldModel]

    def setUpExtra(self):
        self.test_model = test_models.TagFieldModel
        self.tag_model = test_models.TagFieldModel.tags.tag_model

    def test_performance_comparison_1000_instances(self):
        """Performance test: Compare old individual add vs new bulk method with 1000 instances"""
        import time
        from django.db import connection

        # Create 2000 test instances (1000 for each method)
        print(f"\n🏗️  Creating 2000 test instances...")
        instances_old_method = []
        instances_bulk_method = []

        for i in range(1000):
            instances_old_method.append(self.create(self.test_model, name=f"Old_{i}"))
            instances_bulk_method.append(self.create(self.test_model, name=f"Bulk_{i}"))

        print(f"✅ Created {len(instances_old_method) + len(instances_bulk_method)} instances")

        # Enable query logging for this test
        with self.settings(DEBUG=True):

            # METHOD 1: Old individual add() method (1000 instances)
            print(f"\n⏳ Testing OLD method: Adding 'old-method-tag' to 1000 instances individually...")
            old_baseline = len(connection.queries)
            start_time = time.time()

            for instance in instances_old_method:
                instance.tags.add('old-method-tag')

            old_method_time = time.time() - start_time
            old_final = len(connection.queries)
            old_method_queries = old_final - old_baseline

            print(f"🐌 OLD method completed:")
            print(f"   ⏱️  Time: {old_method_time:.2f} seconds")
            print(f"   🗃️  Queries: {old_method_queries}")
            print(f"   📊 Queries per instance: {old_method_queries/1000:.2f}")

            # Verify old method worked
            old_tagged_count = self.test_model.objects.filter(tags__name='old-method-tag').count()
            self.assertEqual(old_tagged_count, 1000)
            old_tag = self.tag_model.objects.get(name='old-method-tag')
            self.assertEqual(old_tag.count, 1000)

            # METHOD 2: New bulk method (1000 instances)
            print(f"\n⚡ Testing NEW bulk method: Adding 'bulk-method-tag' to 1000 instances at once...")
            bulk_baseline = len(connection.queries)
            start_time = time.time()

            created_count = TagRelatedManagerMixin.bulk_add_tag_to_instances(
                tag_name='bulk-method-tag',
                instances=instances_bulk_method,
                tag_field_name='tags'
            )

            bulk_method_time = time.time() - start_time
            bulk_final = len(connection.queries)
            bulk_method_queries = bulk_final - bulk_baseline

            print(f"🚀 NEW bulk method completed:")
            print(f"   ⏱️  Time: {bulk_method_time:.2f} seconds")
            print(f"   🗃️  Queries: {bulk_method_queries}")
            print(f"   📊 Queries per instance: {bulk_method_queries/1000:.3f}")
            print(f"   ✅ Relationships created: {created_count}")

            # Verify bulk method worked
            self.assertEqual(created_count, 1000)
            bulk_tagged_count = self.test_model.objects.filter(tags__name='bulk-method-tag').count()
            self.assertEqual(bulk_tagged_count, 1000)
            bulk_tag = self.tag_model.objects.get(name='bulk-method-tag')
            self.assertEqual(bulk_tag.count, 1000)

            # PERFORMANCE COMPARISON
            time_improvement = old_method_time / bulk_method_time if bulk_method_time > 0 else float('inf')
            query_improvement = old_method_queries / bulk_method_queries if bulk_method_queries > 0 else float('inf')

            print(f"\n📈 PERFORMANCE COMPARISON:")
            print(f"   ⚡ Speed improvement: {time_improvement:.1f}x faster")
            print(f"   🗃️  Query improvement: {query_improvement:.1f}x fewer queries")
            print(f"   💾 Query reduction: {old_method_queries - bulk_method_queries} fewer queries")

            # Assert that bulk method is significantly better
            self.assertGreater(time_improvement, 5.0, "Bulk method should be at least 5x faster")
            self.assertGreater(query_improvement, 2.0, "Bulk method should use at least 2x fewer queries")

            print(f"\n🎉 Performance test completed successfully!")
            print(f"   The bulk method is {time_improvement:.1f}x faster and uses {query_improvement:.1f}x fewer queries!")
