"""
Test models with capitalised names in the database (#60)
"""

from django.test import TestCase

from tests.lib import TagTestManager
from tests.tagulousTestsApp3 import models as test_models


class CapitalisedModelTest(TagTestManager, TestCase):
    """
    Test model with capitalised table name
    """

    manage_models = [test_models.CapitalisedTest]

    def setUpExtra(self):
        self.test_model = test_models.CapitalisedTest
        self.single_tag_model = test_models.CapitalisedTest.singletag.tag_model
        self.single_tag_field = test_models.CapitalisedTest.singletag
        self.tag_model = test_models.CapitalisedTest.tags.tag_model
        self.tag_field = test_models.CapitalisedTest.tags

    def test_table_name_capitalised(self):
        "Check table name is capitalised"
        # since that's what we're here to test
        self.assertEqual(
            self.test_model._meta.db_table, "tagulousTestsApp3_capitalisedtest"
        )
        self.assertEqual(
            self.single_tag_model._meta.db_table,
            "tagulousTestsApp3_tagulous_capitalisedtest_singletag",
        )
        self.assertEqual(
            self.tag_model._meta.db_table,
            "tagulousTestsApp3_tagulous_capitalisedtest_tags",
        )

    def test_tag_basics(self):
        "Check a tag string can be set and get"
        t1 = self.test_model.objects.create(
            name="Test 1", singletag="single1", tags="tag1, tag2"
        )
        self.assertInstanceEqual(
            t1, name="Test 1", singletag="single1", tags="tag1, tag2"
        )

    def test_weight(self):
        "Test weight()"
        # Copy of test_models_tagmodel.TagModelQuerySetTest.test_weight_scale_up
        self.o1 = self.test_model.objects.create(
            name="Test 1", singletag="single1", tags="David, Eric"
        )
        self.o2 = self.test_model.objects.create(
            name="Test 2", singletag="single1", tags="Eric, Frank"
        )

        # Mimic initial from TagFieldOptionsModel
        self.tag_model.objects.create(name="Adam")
        self.tag_model.objects.create(name="Brian")
        self.tag_model.objects.create(name="Chris")

        # Scale them to 2+2n: 0=2, 1=4, 2=6
        weighted = self.tag_model.objects.weight(min=2, max=6)
        self.assertEqual(len(weighted), 6)
        self.assertEqual(weighted[0].name, "Adam")
        self.assertEqual(weighted[0].weight, 2)

        self.assertEqual(weighted[1], "Brian")
        self.assertEqual(weighted[1].weight, 2)

        self.assertEqual(weighted[2], "Chris")
        self.assertEqual(weighted[2].weight, 2)

        self.assertEqual(weighted[3], "David")
        self.assertEqual(weighted[3].weight, 4)

        self.assertEqual(weighted[4], "Eric")
        self.assertEqual(weighted[4].weight, 6)

        self.assertEqual(weighted[5], "Frank")
        self.assertEqual(weighted[5].weight, 4)
