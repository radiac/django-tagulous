"""
Tagulous test: Enhanced queryset for tagged models

Modules tested:
    tagulous.models.queryset.enhance_queryset
"""
from tagulous.tests.lib import *


class ModelEnhancedQuerysetTest(TagTestManager, TestCase):
    """
    Test enhanced querysets
    """
    manage_models = [
        test_models.SingleTagFieldModel,
    ]
    def test_object_get(self):
        "Check that object.get loads the item correctly"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.get(title='Mr')
        self.assertEqual(t1.name, t2.name)
        self.assertEqual(t1.title, t2.title)

    def test_object_filter(self):
        "Check that object.filter finds the correct items"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title='Mrs')
        t3 = test_models.SingleTagFieldModel.objects.create(name='Test 3', title='Mr')
        
        qs1 = test_models.SingleTagFieldModel.objects.filter(title='Mr')
        qs2 = test_models.SingleTagFieldModel.objects.filter(title='Mrs')
        
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(str(qs1[0].title), 'Mr')
        self.assertEqual(str(qs1[0].name), 'Test 1')
        self.assertEqual(str(qs1[1].name), 'Test 3')

        self.assertEqual(qs2.count(), 1)
        self.assertEqual(str(qs2[0].title), 'Mrs')
        self.assertEqual(str(qs2[0].name), 'Test 2')

    def test_object_exclude(self):
        "Check that object.exclude finds the correct items"
        t1 = test_models.SingleTagFieldModel.objects.create(name='Test 1', title='Mr')
        t2 = test_models.SingleTagFieldModel.objects.create(name='Test 2', title='Mrs')
        t3 = test_models.SingleTagFieldModel.objects.create(name='Test 3', title='Mr')
        
        qs1 = test_models.SingleTagFieldModel.objects.exclude(title='Mr')
        qs2 = test_models.SingleTagFieldModel.objects.exclude(title='Mrs')
        
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(str(qs1[0].title), 'Mrs')
        self.assertEqual(str(qs1[0].name), 'Test 2')
        
        self.assertEqual(qs2.count(), 2)
        self.assertEqual(str(qs2[0].title), 'Mr')
        self.assertEqual(str(qs2[0].name), 'Test 1')
        self.assertEqual(str(qs2[1].name), 'Test 3')
