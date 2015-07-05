"""
Tagulous test: Enhanced queryset for tagged models

Modules tested:
    tagulous.models.tagged
"""
from tagulous.tests.lib import *


class ModelEnhancedQuerysetTest(TagTestManager, TestCase):
    """
    Test enhanced querysets
    """
    manage_models = [
        test_models.MixedTest,
    ]
    def test_object_get(self):
        "Check that object.get loads the item correctly"
        t1 = test_models.MixedTest.objects.create(
            name='Test 1', singletag='Mr', tags='blue, green'
        )
        t2 = test_models.MixedTest.objects.get(name='Test 1')
        t3 = test_models.MixedTest.objects.get(singletag='Mr')
        t4 = test_models.MixedTest.objects.get(tags='blue, green')
        self.assertEqual(t1.pk, t2.pk)
        self.assertEqual(t2.pk, t3.pk)
        self.assertEqual(t3.pk, t4.pk)

    def test_object_singletag_filter(self):
        "Check that object.filter finds the correct items by singletag"
        t1 = test_models.MixedTest.objects.create(name='Test 1', singletag='Mr')
        t2 = test_models.MixedTest.objects.create(name='Test 2', singletag='Mrs')
        t3 = test_models.MixedTest.objects.create(name='Test 3', singletag='Mr')
        
        qs1 = test_models.MixedTest.objects.filter(singletag='Mr')
        qs2 = test_models.MixedTest.objects.filter(singletag='Mrs')
        
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(str(qs1[0].singletag), 'Mr')
        self.assertEqual(str(qs1[0].name), 'Test 1')
        self.assertEqual(str(qs1[1].name), 'Test 3')

        self.assertEqual(qs2.count(), 1)
        self.assertEqual(str(qs2[0].singletag), 'Mrs')
        self.assertEqual(str(qs2[0].name), 'Test 2')

    def test_object_exclude(self):
        "Check that object.exclude finds the correct items"
        t1 = test_models.MixedTest.objects.create(name='Test 1', singletag='Mr')
        t2 = test_models.MixedTest.objects.create(name='Test 2', singletag='Mrs')
        t3 = test_models.MixedTest.objects.create(name='Test 3', singletag='Mr')
        
        qs1 = test_models.MixedTest.objects.exclude(singletag='Mr')
        qs2 = test_models.MixedTest.objects.exclude(singletag='Mrs')
        
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(str(qs1[0].singletag), 'Mrs')
        self.assertEqual(str(qs1[0].name), 'Test 2')
        
        self.assertEqual(qs2.count(), 2)
        self.assertEqual(str(qs2[0].singletag), 'Mr')
        self.assertEqual(str(qs2[0].name), 'Test 1')
        self.assertEqual(str(qs2[1].name), 'Test 3')
