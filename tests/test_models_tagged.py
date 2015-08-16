"""
Tagulous test: Enhanced queryset for tagged models

Will fail if settings.ENHANCE_MODELS is not True

Modules tested:
    tagulous.models.tagged
"""
from __future__ import absolute_import
from tests.lib import *

from django.core.exceptions import MultipleObjectsReturned

from tagulous.models.tagged import _split_kwargs



###############################################################################
####### Test _split_kwargs
###############################################################################

class SplitKwargsText(TagTestManager, TestCase):
    "Test _split_kwargs"
    def setUpExtra(self):
        self.test_model = test_models.MixedTest
    
    def test_fields(self):
        "Look up known fields"
        safe_fields, singletag_fields, tag_fields = _split_kwargs(
            self.test_model, {
                'name': 'Adam',
                'singletag': 'Mr',
                'tags': 'red, blue',
            }
        )
        self.assertEqual(len(safe_fields), 1)
        self.assertEqual(safe_fields['name'], 'Adam')
        
        self.assertEqual(len(singletag_fields), 1)
        self.assertEqual(singletag_fields['singletag'], 'Mr')
        
        self.assertEqual(len(tag_fields), 1)
        self.assertEqual(tag_fields['tags'], 'red, blue')

    def test_with_fields(self):
        "Fields dict returned when with_fields"
        safe_fields, singletag_fields, tag_fields, field_lookup = _split_kwargs(
            self.test_model, {
                'name': 'Adam',
                'singletag': 'Mr',
                'tags': 'red, blue',
            }, with_fields=True,
        )
        self.assertEqual(len(safe_fields), 1)
        self.assertEqual(len(singletag_fields), 1)
        self.assertEqual(len(tag_fields), 1)
        
        self.assertEqual(len(field_lookup), 3)
        self.assertEqual(
            field_lookup['name'],
            test_models.MixedTest._meta.get_field('name'),
        )
        self.assertEqual(
            field_lookup['singletag'],
            test_models.MixedTest._meta.get_field('singletag'),
        )
        self.assertEqual(
            field_lookup['tags'],
            test_models.MixedTest._meta.get_field('tags'),
        )
        
    def test_unknown(self):
        "Unknown fields passed as safe"
        safe_fields, singletag_fields, tag_fields = _split_kwargs(
            self.test_model, {
                'unknown':  'field',
            }
        )
        self.assertEqual(len(safe_fields), 1)
        self.assertEqual(safe_fields['unknown'], 'field')
        self.assertEqual(len(singletag_fields), 0)
        self.assertEqual(len(tag_fields), 0)
        
    def test_lookups(self):
        "Test with lookups enabled"
        safe_fields, singletag_fields, tag_fields = _split_kwargs(
            self.test_model, {
                'name__startswith': 'Ad',
                'singletag__name__contains': 'r',
                'tags__name__contains': 'e',
                'tags__exact': 'red, blue',
            }, lookups=True,
        )
        
        # Unknown lookups are passed straight
        self.assertEqual(len(safe_fields), 3)
        self.assertEqual(safe_fields['name__startswith'], 'Ad')
        self.assertEqual(safe_fields['singletag__name__contains'], 'r')
        self.assertEqual(safe_fields['tags__name__contains'], 'e')
        
        self.assertEqual(len(singletag_fields), 0)
        
        self.assertEqual(len(tag_fields), 1)
        self.assertEqual(tag_fields['tags'], ('red, blue', 'exact'))
        
    def test_lookups_normal(self):
        "Test with lookups enabled but normal tag"
        safe_fields, singletag_fields, tag_fields = _split_kwargs(
            self.test_model, {
                'tags': 'red',
            }, lookups=True,
        )
        
        # Unknown lookups are passed straight
        self.assertEqual(len(safe_fields), 0)
        self.assertEqual(len(singletag_fields), 0)
        
        self.assertEqual(len(tag_fields), 1)
        self.assertEqual(tag_fields['tags'], ('red', None))
        
    def test_lookups_unknown(self):
        "Unknown fields in lookups passed as safe"
        safe_fields, singletag_fields, tag_fields = _split_kwargs(
            self.test_model, {
                'unknown__exact':  'field',
            }, lookups=True,
        )
        self.assertEqual(len(safe_fields), 1)
        self.assertEqual(safe_fields['unknown__exact'], 'field')
        self.assertEqual(len(singletag_fields), 0)
        self.assertEqual(len(tag_fields), 0)
    

###############################################################################
####### Test TaggedManager and TaggedQuerySet
###############################################################################
       
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
        self.assertTrue(str(cm.exception).startswith(
            "get() returned more than one MixedTest -- it returned 2!"
        ))
        
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
        self.assertTrue(str(cm.exception).startswith(
            "get() returned more than one MixedTest -- it returned 3!"
        ))
    
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
        self.assertTrue(str(cm.exception).startswith(
            "get() returned more than one MixedTest -- it returned 2!"
        ))
    
    def test_object_get_by_singletag_tags(self):
        "Check that object.get singletag and tags loads the item correctly"
        t1 = self.test_model.objects.get(singletag='Mr', tags='red, blue')
        self.assertEqual(t1.pk, self.o1.pk)
        
    
    #
    # .get_or_create()
    #
    
    def test_object_get_or_create_singletagfield(self):
        "Check that objects.get_or_create on SingleTagField creates and gets"
        # Clear out models
        self.test_model.objects.all().delete()
        self.test_model.singletag.tag_model.objects.all().delete()
        self.assertTagModel(self.test_model.singletag, {})
        
        # Create
        t1, created = self.test_model.objects.get_or_create(
            singletag='Mr',
        )
        self.assertEqual(created, True)
        self.assertTagModel(self.test_model.singletag, {'Mr': 1})
        t1.name = 'Test 4'
        t1.save()
        self.assertEqual(str(t1.singletag), 'Mr')
        
        # Get
        t2, created = self.test_model.objects.get_or_create(
            singletag='Mr',
        )
        self.assertEqual(created, False)
        self.assertTagModel(self.test_model.singletag, {'Mr': 1})
        self.assertEqual(t2.name, 'Test 4')
        self.assertEqual(str(t2.singletag), 'Mr')
        
        self.assertEqual(t1.pk, t2.pk)
            
    def test_object_get_or_create_tagfield(self):
        "Check that objects.get_or_create on TagField creates and gets"
        # Clear out models
        self.test_model.objects.all().delete()
        self.test_model.tags.tag_model.objects.all().delete()
        self.assertTagModel(self.test_model.tags, {})
        
        # Create
        t1, created = self.test_model.objects.get_or_create(
            tags='red, blue',
        )
        self.assertEqual(created, True)
        self.assertTagModel(self.test_model.tags, {'red': 1, 'blue': 1})
        t1.name = 'Test 4'
        t1.save()
        self.assertEqual(str(t1.tags), 'blue, red')
        
        # Get
        t2, created = self.test_model.objects.get_or_create(
            tags='red, blue',
        )
        self.assertEqual(created, False)
        self.assertTagModel(self.test_model.tags, {'red': 1, 'blue': 1})
        self.assertEqual(t2.name, 'Test 4')
        self.assertEqual(str(t1.tags), 'blue, red')
        
        self.assertEqual(t1.pk, t2.pk)
        
    
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
    
    def test_object_tags_filter_none(self):
        "Check that object.filter returns objects with no tags"
        o4 = self.test_model.objects.create(name='Test 4', tags='')
        qs1 = self.test_model.objects.filter(tags=None)
        self.assertEqual(qs1.count(), 1)
        self.assertEqual(qs1[0].pk, o4.pk)
    
    
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
        
    def test_object_tags_exclude_none(self):
        "Check that object.exclude returns objects with tags"
        o4 = self.test_model.objects.create(name='Test 4', tags='')
        qs1 = self.test_model.objects.exclude(tags=None)
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
        

###############################################################################
####### Test TaggedModel
###############################################################################
       
class ModelTaggedTest(TagTestManager, TestCase):
    """
    Test parts of TaggedModel not caught by other tests
    """
    manage_models = [
        test_models.MixedTest,
    ]
    def setUpExtra(self):
        self.test_model = test_models.MixedTest
    
    def test_init(self):
        "Check constructor can set singletag and tag fields"
        t1 = self.test_model(
            name='Test 1',
            singletag='Mr',
            tags='red, blue',
        )
        t1.save()
        t2 = self.test_model.objects.get(name='Test 1')
        self.assertEqual(str(t2.singletag), 'Mr')
        self.assertEqual(str(t2.tags), 'blue, red')
