"""
Tagulous test: Enhanced queryset for tagged models

Modules tested:
    tagulous.models.tagged
"""
from tagulous.tests.lib import *

from django.core.exceptions import MultipleObjectsReturned


class ModelTaggedQuerysetTest(TagTestManager, TestCase):
    """
    Test enhanced tagged model querysets
    """
    manage_models = [
        test_models.MixedTest,
    ]
    def setUpExtra(self):
        self.test_model = test_models.MixedTest
        
        self.o1 = self.test_model.objects.create(
            name='Test 1', singletag='Mr', tags='red, green, blue',
        )
        self.o2 = self.test_model.objects.create(
            name='Test 2', singletag='Mrs', tags='red, green, blue',
        )
        self.o3 = self.test_model.objects.create(
            name='Test 3', singletag='Mr', tags='red, green',
        )
    
    
    #
    # .get()
    #
    
    def test_object_get_by_singletag(self):
        "Check that object.get singletag loads the item correctly"
        t1 = self.test_model.objects.get(singletag='Mrs')
        self.assertEqual(t1.pk, self.o2.pk)
        
    def test_object_get_by_singletag_multiple_raises(self):
        "Check that object.get singletag raises exception when multiple found"
        with self.assertRaises(MultipleObjectsReturned) as cm:
            t1 = self.test_model.objects.get(singletag='Mr')
        self.assertEqual(
            str(cm.exception),
            "get() returned more than one MixedTest -- it returned 2!"
        )
        
    def test_object_get_by_tags(self):
        "Check that object.get tags loads the item correctly"
        o4 = self.test_model.objects.create(
            name='Test 4', tags='red, green, yellow',
        )
        t1 = self.test_model.objects.get(tags='red, yellow')
        self.assertEqual(t1.pk, o4.pk)

    def test_object_get_by_tags_multiple_raises(self):
        "Check that object.get tags raises exception when multiple found"
        with self.assertRaises(MultipleObjectsReturned) as cm:
            t1 = self.test_model.objects.get(tags='red, green')
        self.assertEqual(
            str(cm.exception),
            "get() returned more than one MixedTest -- it returned 3!"
        )
    
    def test_object_get_by_tags_exact(self):
        "Check that object.get tags loads the item correctly"
        t1 = self.test_model.objects.get(tags__exact='red, green')
        self.assertEqual(t1.pk, self.o3.pk)

    def test_object_get_by_tags_multiple_exact_raises(self):
        "Check that object.get tags raises exception when multiple found"
        o4 = self.test_model.objects.create(
            name='Test 4', tags='yellow, purple',
        )
        o5 = self.test_model.objects.create(
            name='Test 5', tags='yellow, purple',
        )
        with self.assertRaises(MultipleObjectsReturned) as cm:
            t1 = self.test_model.objects.get(tags__exact='yellow, purple')
        self.assertEqual(
            str(cm.exception),
            "get() returned more than one MixedTest -- it returned 2!"
        )
    
    def test_object_get_by_singletag_tags(self):
        "Check that object.get singletag and tags loads the item correctly"
        t1 = self.test_model.objects.get(singletag='Mr', tags='red, blue')
        self.assertEqual(t1.pk, self.o1.pk)

    
    #
    # .filter()
    #
    
    def test_object_singletag_filter(self):
        "Check that object.filter finds the correct items by singletag"
        qs1 = self.test_model.objects.filter(singletag='Mr')
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o3.pk)

    def test_object_singletag_filter_misses(self):
        "Check that object.filter copes with missing singletag"
        qs1 = self.test_model.objects.filter(singletag='Miss')
        self.assertEqual(qs1.count(), 0)
        
    def test_object_tags_filter(self):
        "Check that object.filter finds the correct items by tags"
        qs1 = self.test_model.objects.filter(tags='red, blue')
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o2.pk)
        
    def test_object_tags_filter_exact(self):
        "Check that object.filter finds the correct items by tags"
        qs1 = self.test_model.objects.filter(tags__exact='red, green, blue')
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o2.pk)
        
    def test_object_tags_filter_exact_misses(self):
        "Check that object.filter only returns exact matches"
        qs1 = self.test_model.objects.filter(tags__exact='red, blue')
        self.assertEqual(qs1.count(), 0)
    
    
    #
    # .exclude()
    #
    
    def test_object_singletag_exclude(self):
        "Check that object.exclude finds the correct items"
        qs1 = self.test_model.objects.exclude(singletag='Mrs')
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o3.pk)
    
    def test_object_singletag_exclude_misses(self):
        "Check that object.exclude copes with missing singletag"
        qs1 = self.test_model.objects.exclude(singletag='Miss')
        self.assertEqual(qs1.count(), 3)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o2.pk)
        self.assertEqual(qs1[2].pk, self.o3.pk)
    
    def test_object_tags_exclude(self):
        "Check that object.exclude excludes when both are matched"
        qs1 = self.test_model.objects.exclude(tags='red, blue')
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs1[0].pk, self.o3.pk)
    
    def test_object_tags_exclude_misses(self):
        "Check that object.exclude copes with missing tag"
        qs1 = self.test_model.objects.exclude(tags='red, yellow')
        self.assertEqual(qs1.count(), 3)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o2.pk)
        self.assertEqual(qs1[2].pk, self.o3.pk)
        
    def test_object_tags_exclude_exact(self):
        "Check that object.exclude exact excludes by tags"
        qs1 = self.test_model.objects.exclude(tags='red, green, blue')
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs1[0].pk, self.o3.pk)
    
    def test_object_tags_exclude_exact_misses(self):
        "Check that object.exclude only excludes exact matches"
        qs1 = self.test_model.objects.exclude(tags='red, green, yellow')
        self.assertEqual(qs1.count(), 3)
        self.assertEqual(qs1[0].pk, self.o1.pk)
        self.assertEqual(qs1[1].pk, self.o2.pk)
        self.assertEqual(qs1[2].pk, self.o3.pk)
    
    
class ModelTaggedQuerysetOptionsSingleTest(TagTestManager, TestCase):
    """
    Test tag options on tagged model querysets, for SingleTagField
    
    The only tag options which should be applied to queryset arguments is
    case_sensitive
    """
    manage_models = [
        test_models.SingleTagFieldOptionsModel,
    ]
    def setUpExtra(self):
        self.test_model = test_models.SingleTagFieldOptionsModel
        t1 = self.test_model.objects.create(
            name='Test 1',
            case_sensitive_true='Mr',
            case_sensitive_false='Mr',
        )
        t2 = self.test_model.objects.create(
            name='Test 2',
            case_sensitive_true='mr',
            case_sensitive_false='mr',
        )
        t3 = self.test_model.objects.create(
            name='Test 3',
            case_sensitive_true='Mr',
            case_sensitive_false='Mr',
        )
    
    def test_setup(self):
        "Confirm setup created objects as expected"
        self.assertTagModel(self.test_model.case_sensitive_true, {
            'Mr':     2,
            'mr':     1,
        })
        self.assertTagModel(self.test_model.case_sensitive_false, {
            'Mr':     3,
        })
        
    def test_case_sensitive_filter(self):
        "Check case sensitive matches"
        qs1 = self.test_model.objects.filter(case_sensitive_true='Mr')
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(str(qs1[0].name), 'Test 1')
        self.assertEqual(str(qs1[1].name), 'Test 3')

    def test_case_sensitive_exclude_matches(self):
        "Check case sensitive excludes"
        qs1 = self.test_model.objects.exclude(case_sensitive_true='Mr')
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(str(qs1[0].name), 'Test 2')
    
    def test_case_insensitive_filter(self):
        "Check case insensitive matches"
        qs1 = self.test_model.objects.filter(case_sensitive_false='mr')
        self.assertEqual(qs1.count(), 3)
        self.assertEqual(str(qs1[0].name), 'Test 1')
        self.assertEqual(str(qs1[1].name), 'Test 2')
        self.assertEqual(str(qs1[2].name), 'Test 3')
        
    def test_case_insensitive_exclude(self):
        "Check case insensitive matches"
        qs1 = self.test_model.objects.exclude(case_sensitive_false='mr')
        self.assertEqual(qs1.count(), 0)
        

class ModelTaggedQuerysetOptionsTest(TagTestManager, TestCase):
    """
    Test tag options on tagged model querysets, for TagField
    
    The only tag options which should be applied to queryset arguments is
    case_sensitive
    """
    manage_models = [
        test_models.TagFieldOptionsModel,
    ]
    def setUpExtra(self):
        self.test_model = test_models.TagFieldOptionsModel
        t1 = self.test_model.objects.create(
            name='Test 1',
            case_sensitive_true='Adam',
            case_sensitive_false='Adam',
        )
        t2 = self.test_model.objects.create(
            name='Test 2',
            case_sensitive_true='adam',
            case_sensitive_false='adam',
        )
        t3 = self.test_model.objects.create(
            name='Test 3',
            case_sensitive_true='Adam',
            case_sensitive_false='Adam',
        )
    
    def test_setup(self):
        "Confirm setup created objects as expected"
        self.assertTagModel(self.test_model.case_sensitive_true, {
            'Adam':     2,
            'adam':     1,
        })
        self.assertTagModel(self.test_model.case_sensitive_false, {
            'Adam':     3,
        })
        
    def test_case_sensitive_filter(self):
        "Check case sensitive matches"
        qs1 = self.test_model.objects.filter(case_sensitive_true='Adam')
        self.assertEqual(qs1.count(), 2)
        self.assertEqual(str(qs1[0].name), 'Test 1')
        self.assertEqual(str(qs1[1].name), 'Test 3')

    def test_case_sensitive_exclude_matches(self):
        "Check case sensitive excludes"
        qs1 = self.test_model.objects.exclude(case_sensitive_true='Adam')
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(str(qs1[0].name), 'Test 2')
    
    def test_case_insensitive_filter(self):
        "Check case insensitive matches"
        qs1 = self.test_model.objects.filter(case_sensitive_false='adam')
        self.assertEqual(qs1.count(), 3)
        self.assertEqual(str(qs1[0].name), 'Test 1')
        self.assertEqual(str(qs1[1].name), 'Test 2')
        self.assertEqual(str(qs1[2].name), 'Test 3')
        
    def test_case_insensitive_exclude(self):
        "Check case insensitive matches"
        qs1 = self.test_model.objects.exclude(case_sensitive_false='adam')
        self.assertEqual(qs1.count(), 0)
        
