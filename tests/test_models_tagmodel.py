# -*- coding: utf-8 -*-
"""
Tagulous test: Tag models

Modules tested:
    tagulous.models.models.BaseTagModel
    tagulous.models.models.TagModel
    tagulous.models.models.TagModelManager
    tagulous.models.models.TagModelQuerySet
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from tests.lib import *


class TagModelTest(TagTestManager, TestCase):
    """
    Test tag model basics
    """
    manage_models = [
        test_models.MixedTest,
        test_models.MixedRefTest,
        test_models.NonTagRefTest,
    ]
    
    def setUpExtra(self):
        self.tag_model = test_models.MixedTestTagModel
        self.model1 = test_models.MixedTest
        self.model2 = test_models.MixedRefTest
        self.model_nontag = test_models.NonTagRefTest
    
    def test_tags_equal_instance(self):
        "Test TagModel.__eq__ with instances"
        t1a = self.tag_model.objects.create(name='one')
        t1b = self.tag_model.objects.get(name='one')
        self.assertEqual(t1a, t1b)

    def test_tags_equal_string(self):
        "Test TagModel.__eq__ with instance and string"
        t1 = self.tag_model.objects.create(name='one')
        self.assertEqual(t1, 'one')

    def test_tags_not_equal_instance(self):
        "Test TagModel.__ne__ with instances"
        t1 = self.tag_model.objects.create(name='one')
        t2 = self.tag_model.objects.create(name='two')
        self.assertNotEqual(t1, t2)

    def test_tags_not_equal_string(self):
        "Test TagModel.__eq__ with instance and string"
        t1 = self.tag_model.objects.create(name='one')
        self.assertNotEqual(t1, 'two')
    
    def test_get_absolute_url_defined(self):
        "Test get_absolute_url when passed in field definition"
        t1 = self.tag_model.objects.create(name='one')
        self.assertEqual(t1.get_absolute_url(), 'url for one')
    
    def test_get_absolute_url_not_defined(self):
        "Test get_absolute_url when passed in field definition"
        t1 = test_models.SimpleMixedTest.tags.tag_model.objects.create(name='one')
        with self.assertRaises(AttributeError) as cm:
            t1.get_absolute_url()
        self.assertEqual(
            six.text_type(cm.exception),
            "'_Tagulous_SimpleMixedTest_tags' has no attribute 'get_absolute_url'"
        )
    
    def assertRelatedExists(self, related_fields, match_model, field_name):
        """
        Look through the related fields and find the field which refers to the
        specified model; fail if it does not exist
        """
        match_field = match_model._meta.get_field(field_name)
        for related in related_fields:
            if django.VERSION < (1, 8):
                rel_model = related.model
            else:
                rel_model = related.related_model
            
            if rel_model == match_model and related.field == match_field:
                return related
        self.fail('Expected related field not found')
    
    def test_get_related_fields(self):
        "Check the class method returns a list of related fields"
        related_fields = self.tag_model.get_related_fields()
        self.assertEqual(len(related_fields), 4)
        
        # FK comes before M2M, so first two will be the SingleTagFields
        self.assertRelatedExists(related_fields, self.model1, 'singletag')
        self.assertRelatedExists(related_fields, self.model2, 'singletag')
        
        # Now the TagFields
        self.assertRelatedExists(related_fields, self.model1, 'tags')
        self.assertRelatedExists(related_fields, self.model2, 'tags')
    
    def test_get_related_fields_standard(self):
        "Check the class method can also find standard relationships"
        related_fields = self.tag_model.get_related_fields(include_standard=True)
        self.assertEqual(len(related_fields), 6)
        
        # SingleTagFields/FKs
        self.assertRelatedExists(related_fields, self.model1, 'singletag')
        self.assertRelatedExists(related_fields, self.model2, 'singletag')
        self.assertRelatedExists(related_fields, self.model_nontag, 'fk')
        
        # TagFields/M2Ms
        self.assertRelatedExists(related_fields, self.model1, 'tags')
        self.assertRelatedExists(related_fields, self.model2, 'tags')
        self.assertRelatedExists(related_fields, self.model_nontag, 'mm')
        
    def test_get_related_objects(self):
        """
        Check the class method returns a list of related models, fields and
        instances
        """
        t1 = self.create(self.model1, name="Test 1", singletag='Mr', tags='blue')
        t2 = self.create(self.model1, name="Test 2", singletag='Mr', tags='green')
        t3 = self.create(self.model2, name="Test 3", singletag='Mrs', tags='green')
        t4 = self.create(self.model2, name="Test 4", singletag='Mr', tags='green')
        
        #
        # Check Mr
        #
        singletag1 = self.tag_model.objects.get(name='Mr')
        rel_st1 = singletag1.get_related_objects()
        self.assertEqual(len(rel_st1), 2)
        # Don't assume order - we could probably guess reliably, but
        # why risk it in tests
        # rel_st1 is list of [model, field, [instances]]
        if rel_st1[0][0] == self.model1:
            rel_st1_m1 = rel_st1[0]
            rel_st1_m2 = rel_st1[1]
        else:
            rel_st1_m1 = rel_st1[1]
            rel_st1_m2 = rel_st1[0]
            
        self.assertEqual(rel_st1_m1[0], self.model1)
        self.assertEqual(rel_st1_m1[1], self.model1._meta.get_field('singletag'))
        self.assertEqual(len(rel_st1_m1[2]), 2)
        self.assertEqual(rel_st1_m1[2][0], t1)
        self.assertEqual(rel_st1_m1[2][1], t2)
        
        self.assertEqual(rel_st1_m2[0], self.model2)
        self.assertEqual(rel_st1_m2[1], self.model2._meta.get_field('singletag'))
        self.assertEqual(len(rel_st1_m2[2]), 1)
        self.assertEqual(rel_st1_m2[2][0], t4)
        
        #
        # Check Mrs
        #
        singletag2 = self.tag_model.objects.get(name='Mrs')
        rel_st2 = singletag2.get_related_objects()
        self.assertEqual(len(rel_st2), 1)
        rel_st2_m1 = rel_st2[0]
        self.assertEqual(rel_st2_m1[0], self.model2)
        self.assertEqual(rel_st2_m1[1], self.model2._meta.get_field('singletag'))
        self.assertEqual(len(rel_st2_m1[2]), 1)
        self.assertEqual(rel_st2_m1[2][0], t3)
        
        #
        # Check blue
        #
        tags1 = self.tag_model.objects.get(name='blue')
        rel_t1 = tags1.get_related_objects()
        self.assertEqual(len(rel_t1), 1)
        rel_t1_m1 = rel_t1[0]
        self.assertEqual(rel_t1_m1[0], self.model1)
        self.assertEqual(rel_t1_m1[1], self.model1._meta.get_field('tags'))
        self.assertEqual(len(rel_t1_m1[2]), 1)
        self.assertEqual(rel_t1_m1[2][0], t1)
        
        #
        # Check green
        #
        tags2 = self.tag_model.objects.get(name='green')
        rel_t2 = tags2.get_related_objects()
        self.assertEqual(len(rel_t2), 2)
        if rel_t2[0][0] == self.model1:
            rel_t2_m1 = rel_t2[0]
            rel_t2_m2 = rel_t2[1]
        else:
            rel_t2_m1 = rel_t2[1]
            rel_t2_m2 = rel_t2[0]

        self.assertEqual(rel_t2_m1[0], self.model1)
        self.assertEqual(rel_t2_m1[1], self.model1._meta.get_field('tags'))
        self.assertEqual(len(rel_t2_m1[2]), 1)
        self.assertEqual(rel_t2_m1[2][0], t2)
        
        self.assertEqual(rel_t2_m2[0], self.model2)
        self.assertEqual(rel_t2_m2[1], self.model2._meta.get_field('tags'))
        self.assertEqual(len(rel_t2_m2[2]), 2)
        self.assertEqual(rel_t2_m2[2][0], t3)
        self.assertEqual(rel_t2_m2[2][1], t4)
        
    def test_get_related_objects_flat(self):
        "Check the class method returns a flat list of related instances"
        t1 = self.create(self.model1, name="Test 1", singletag='Mr', tags='blue')
        t2 = self.create(self.model1, name="Test 2", singletag='Mr', tags='green')
        t3 = self.create(self.model2, name="Test 3", singletag='Mrs', tags='green')
        t4 = self.create(self.model2, name="Test 4", singletag='Mr', tags='green')
        
        # Check Mr
        singletag1 = self.tag_model.objects.get(name='Mr')
        rel_st1 = singletag1.get_related_objects(flat=True)
        self.assertEqual(len(rel_st1), 3)
        rel_st1.sort(key=lambda tag: tag.name)
        self.assertEqual(rel_st1[0], t1)
        self.assertEqual(rel_st1[1], t2)
        self.assertEqual(rel_st1[2], t4)
        
        # Check Mrs
        singletag2 = self.tag_model.objects.get(name='Mrs')
        rel_st2 = singletag2.get_related_objects(flat=True)
        self.assertEqual(len(rel_st2), 1)
        self.assertEqual(rel_st2[0], t3)
        
        # Check blue
        tags1 = self.tag_model.objects.get(name='blue')
        rel_t1 = tags1.get_related_objects(flat=True)
        self.assertEqual(len(rel_t1), 1)
        self.assertEqual(rel_t1[0], t1)
        
        # Check green
        tags2 = self.tag_model.objects.get(name='green')
        rel_t2 = tags2.get_related_objects(flat=True)
        self.assertEqual(len(rel_t2), 3)
        rel_t2.sort(key=lambda tag: tag.name)
        self.assertEqual(rel_t2[0], t2)
        self.assertEqual(rel_t2[1], t3)
        self.assertEqual(rel_t2[2], t4)
        
    def test_get_related_objects_flat_distinct(self):
        "Check the class method returns a flat list of distinct related instances"
        t1 = self.create(self.model1, name="Test 1", singletag='Mr', tags='blue')
        t2 = self.create(self.model2, name="Test 2", singletag='blue', tags='blue')
        
        # Check blue non-distinct
        tags1 = self.tag_model.objects.get(name='blue')
        rel_t1 = tags1.get_related_objects(flat=True)
        self.assertEqual(len(rel_t1), 3)
        rel_t1.sort(key=lambda tag: tag.name)
        self.assertEqual(rel_t1[0], t1)
        self.assertEqual(rel_t1[1], t2)
        self.assertEqual(rel_t1[2], t2)
        
        # Check blue distinct
        rel_t2 = tags1.get_related_objects(flat=True, distinct=True)
        self.assertEqual(len(rel_t2), 2)
        rel_t2.sort(key=lambda tag: tag.name)
        self.assertEqual(rel_t2[0], t1)
        self.assertEqual(rel_t2[1], t2)
 
    def test_get_related_objects_flat_include_standard(self):
        """
        Check the class method returns a flat list of related instances,
        including standard relationships
        
        No need to test other options with include_standard, uses same code
        """
        t1 = self.create(self.model1, name="Test 1", singletag='Mr', tags='blue')
        singletag1 = self.tag_model.objects.get(name='Mr')
        tags1 = self.tag_model.objects.get(name='blue')
        t2 = self.create(self.model_nontag, name="Test 2", fk=singletag1, mm=[tags1])
        
        # Check Mr
        rel_st1 = singletag1.get_related_objects(flat=True, include_standard=True)
        self.assertEqual(len(rel_st1), 2)
        rel_st1.sort(key=lambda tag: tag.name)
        self.assertEqual(rel_st1[0], t1)
        self.assertEqual(rel_st1[1], t2)
        
        # Check blue
        rel_t1 = tags1.get_related_objects(flat=True, include_standard=True)
        self.assertEqual(len(rel_t1), 2)
        rel_t1.sort(key=lambda tag: tag.name)
        self.assertEqual(rel_t1[0], t1)
        self.assertEqual(rel_t1[1], t2)
        
    def test_increment(self):
        "Increment the tag count"
        tag1 = self.create(self.tag_model, name='blue')
        self.assertInstanceEqual(tag1, count=0)
        tag1.increment()
        self.assertInstanceEqual(tag1, count=1)
    
    def test_increment_db(self):
        "Increment the tag count using the DB value, not in-memory"
        tag1 = self.create(self.tag_model, name='blue')
        tag2 = self.tag_model.objects.get(pk=tag1.pk)
        self.assertEqual(tag1.count, 0)
        self.assertEqual(tag2.count, 0)
        
        tag1.increment()
        self.assertInstanceEqual(tag1, count=1)
        self.assertInstanceEqual(tag2, count=1)
        self.assertEqual(tag1.count, 1)
        self.assertEqual(tag2.count, 0)
        
        tag2.increment()
        self.assertInstanceEqual(tag1, count=2)
        self.assertInstanceEqual(tag2, count=2)
        self.assertEqual(tag1.count, 1)
        self.assertEqual(tag2.count, 2)
    
    def test_decrement(self):
        tag1 = self.create(self.tag_model, name='blue', count=2)
        self.assertTagModel(self.tag_model, {
            'blue': 2,
        })
        tag1.decrement()
        self.assertTagModel(self.tag_model, {
            'blue': 1,
        })
        
    def test_decrement_delete(self):
        tag1 = self.create(self.tag_model, name='blue', count=1)
        self.assertTagModel(self.tag_model, {
            'blue': 1,
        })
        tag1.decrement()
        self.assertTagModel(self.tag_model, {})
    
    def test_decrement_delete_protected(self):
        tag1 = self.create(self.tag_model, name='blue', count=1, protected=True)
        self.assertTagModel(self.tag_model, {
            'blue': 1,
        })
        tag1.decrement()
        self.assertTagModel(self.tag_model, {
            'blue': 0,
        })
        
    def test_decrement_delete_hasrefs(self):
        """
        Check that when a tag's count hits 0, but still has non-tag field
        references, that it isn't deleted - don't want to cascade/break refs
        """
        # Create tags with false count
        tag1 = self.create(self.tag_model, name='blue', count=1)
        tag2 = self.create(self.tag_model, name='red', count=1)
        self.assertTagModel(self.tag_model, {
            'blue': 1,
            'red':  1,
        })
        
        # Create object with conventional references to tags
        t1 = self.create(
            self.model_nontag, name="Non-tag field", fk=tag1, mm=[tag2]
        )
        self.assertInstanceEqual(
            t1, name="Non-tag field", fk=tag1, mm=[tag2]
        )
        
        # No change to count
        self.assertTagModel(self.tag_model, {
            'blue': 1,
            'red':  1,
        })
        
        # Check get_related_objects knows about them
        self.assertEqual(
            len(tag1.get_related_objects(flat=True, include_standard=True)), 1
        )
        self.assertEqual(
            len(tag2.get_related_objects(flat=True, include_standard=True)), 1
        )
        
        # Now decrement counts to 0, but tags remain
        tag1.decrement()
        tag2.decrement()
        self.assertTagModel(self.tag_model, {
            'blue': 0,
            'red':  0,
        })

    def test_update_count(self):
        "Purposely knock the count off and update it"
        t1 = self.create(self.model1, name="Test 1", tags='blue')
        tag1 = self.tag_model.objects.get(name='blue')
        self.assertTagModel(self.tag_model, {'blue': 1})
        tag1.count = 3
        tag1.save()
        self.assertTagModel(self.tag_model, {'blue': 3})
        tag1.update_count()
        self.assertTagModel(self.tag_model, {'blue': 1})
        t1.delete()
        self.assertTagModel(self.tag_model, {})
        
    def test_slug_set(self):
        "Check the slug field is set correctly"
        t1a = self.tag_model.objects.create(name='One and Two!')
        self.assertEqual(t1a.slug, 'one-and-two')
        
    def test_slug_saved(self):
        "Check the slug field is saved correctly"
        t1a = self.tag_model.objects.create(name='One and Two!')
        t1b = self.tag_model.objects.get(name='One and Two!')
        self.assertEqual(t1a.slug, t1b.slug)
        self.assertEqual(t1b.slug, 'one-and-two')

    def test_slug_clash(self):
        "Check slug field avoids clashes to remain unique"
        t1a = self.tag_model.objects.create(name='one and two')
        t2a = self.tag_model.objects.create(name='One and Two!')
        t3a = self.tag_model.objects.create(name='One and Two?')
        t4a = self.tag_model.objects.create(name='One and Two.')
        self.assertEqual(t1a.slug, 'one-and-two')
        self.assertEqual(t2a.slug, 'one-and-two_1')
        self.assertEqual(t3a.slug, 'one-and-two_2')
        self.assertEqual(t4a.slug, 'one-and-two_3')
        
        t1b = self.tag_model.objects.get(name='one and two')
        t2b = self.tag_model.objects.get(name='One and Two!')
        t3b = self.tag_model.objects.get(name='One and Two?')
        t4b = self.tag_model.objects.get(name='One and Two.')
        self.assertEqual(t1b.slug, 'one-and-two')
        self.assertEqual(t2b.slug, 'one-and-two_1')
        self.assertEqual(t3b.slug, 'one-and-two_2')
        self.assertEqual(t4b.slug, 'one-and-two_3')


###############################################################################
####### Test TagMeta in tag model
###############################################################################

class TagMetaTest(TagTestManager, TestCase):
    """
    Test TagMeta class. Builds on tests in tests_options.
    """
    def test_sets_options(self):
        "Check TagMeta sets the options"
        opt = test_models.TagMetaAbstractModel.tag_options
        
        # Check local options
        cls_opt = opt.items(with_defaults=False)
        self.assertEqual(cls_opt['initial'], ['Adam', 'Brian', 'Chris'])
        self.assertEqual(cls_opt['force_lowercase'], True)
        self.assertEqual(cls_opt['max_count'], 5)
        self.assertTrue('case_sensitive' not in cls_opt)
        
        # Check default options
        self.assertEqual(opt.case_sensitive, False)
    
    def test_inheritance(self):
        "Check TagMeta can be inherited and overridden"
        opt_abstract = test_models.TagMetaAbstractModel.tag_options
        opt = test_models.TagMetaModel.tag_options
        
        # Check they're not shared instances
        self.assertNotEqual(id(opt_abstract), id(opt))
        self.assertNotEqual(id(opt), id(tag_models.models.BaseTagModel.tag_options))
        
        # Check local options
        cls_opt = opt.items(with_defaults=False)
        self.assertEqual(cls_opt['case_sensitive'], True)
        self.assertEqual(cls_opt['max_count'], 10)
        
        # Local options will also include inherited options
        self.assertEqual(opt.initial, ['Adam', 'Brian', 'Chris'])
        self.assertEqual(opt.force_lowercase, True)
        self.assertEqual(opt.max_count, 10)
        self.assertEqual(opt.case_sensitive, True)


###############################################################################
####### Test unicode in tag model
###############################################################################

class TagModelUnicodeTest(TagTestManager, TestCase):
    """
    Test unicode tags - forced to not use unidecode, even if available
    """
    manage_models = [
        test_models.MixedTest,
    ]
    
    def setUpExtra(self):
        # Disable unidecode support
        self.unidecode_status = tag_utils.unidecode
        tag_utils.unidecode = None
        
        self.model = test_models.MixedTest
        self.tag_model = test_models.MixedTestTagModel
        self.o1 = self.create(
            self.model, name="Test",
            singletag='男の子',
            tags='boy, niño, 男の子',
        )
    
    def tearDownExtra(self):
        tag_utils.unidecode = self.unidecode_status
        
    def test_setup(self):
        "Check setup created tags as expected"
        self.assertTagModel(self.tag_model, {
            'boy':     1,
            'niño':    1,
            '男の子':   2,
        })
    
    
    # Check lookup
    
    def test_get_singletag_get(self):
        "Check unicode singletag name matches"
        t1 = self.model.objects.get(singletag='男の子')
        self.assertEqual(t1.pk, self.o1.pk)
        
    def test_get_tag_ascii(self):
        "Check unicode tag name matches when ascii"
        t1 = self.model.objects.get(tags='boy')
        self.assertEqual(t1.pk, self.o1.pk)
        
    def test_get_tag_extended_ascii(self):
        "Check unicode tag name matches when extended ascii"
        t1 = self.model.objects.get(tags='niño')
        self.assertEqual(t1.pk, self.o1.pk)
        
    def test_get_tag_japanese(self):
        "Check unicode tag name matches when above extended ascii"
        t1 = self.model.objects.get(tags='男の子')
        self.assertEqual(t1.pk, self.o1.pk)
    
    
    # Check render
    
    def test_singletag_render(self):
        "Check unicode singletag name renders"
        t1 = self.model.objects.get(name="Test")
        self.assertEqual(six.text_type(t1.singletag), '男の子')
        
    def test_tag_render(self):
        "Check unicode tag name renders"
        t1 = self.model.objects.get(name="Test")
        tags = list(t1.tags.all())
        self.assertEqual(six.text_type(tags[0]), 'boy')
        self.assertEqual(six.text_type(tags[1]), 'niño')
        self.assertEqual(six.text_type(tags[2]), '男の子')
        
    def test_tag_string_render(self):
        "Check unicode tags string renders"
        t1 = self.model.objects.get(name="Test")
        self.assertEqual(six.text_type(t1.tags), 'boy, niño, 男の子')


    # Check slugs
    
    def test_slug_ascii(self):
        "Check unicode tag name slugified when ascii"
        t1 = self.tag_model.objects.get(name="boy")
        self.assertEqual(t1.slug, 'boy')
    
    def test_slug_extended_ascii(self):
        "Check unicode tag name slugified when ascii"
        t1 = self.tag_model.objects.get(name="niño")
        self.assertEqual(t1.slug, 'nino')
        
    def test_slug_japanese(self):
        "Check unicode tag name slugified when ascii"
        t1 = self.tag_model.objects.get(name="男の子")
        self.assertEqual(t1.slug, '___')


try:
    from unidecode import unidecode
except ImportError:
    unidecode = None

@unittest.skipIf(unidecode is None, 'optional unidecode not installed')
class TagModelUnicodeUnidecodeTest(TagTestManager, TestCase):
    """
    Test unicode tags, without using unidecode
    
    This only affects slugs 
    """
    manage_models = [
        test_models.MixedTest,
    ]
    
    def setUpExtra(self):
        self.model = test_models.MixedTest
        self.tag_model = test_models.MixedTestTagModel
        self.o1 = self.create(
            self.model, name="Test",
            singletag='男の子',
            tags='boy, niño, 男の子',
        )
    
    def test_setup(self):
        "Check setup created tags as expected"
        self.assertTagModel(self.tag_model, {
            'boy':     1,
            'niño':    1,
            '男の子':   2,
        })
    
    
    # unidecode only affects slugs
    
    def test_slug_ascii(self):
        "Check unicode tag name slugified when ascii"
        t1 = self.tag_model.objects.get(name="boy")
        self.assertEqual(t1.slug, 'boy')
    
    def test_slug_extended_ascii(self):
        "Check unicode tag name slugified when ascii"
        t1 = self.tag_model.objects.get(name="niño")
        self.assertEqual(t1.slug, 'nino')
        
    def test_slug_japanese(self):
        "Check unicode tag name slugified when ascii"
        t1 = self.tag_model.objects.get(name="男の子")
        self.assertEqual(t1.slug, 'nan-nozi')
    

###############################################################################
####### Test tag merging
###############################################################################

class TagModelMergeTest(TagTestManager, TestCase):
    """
    Test tag merging
    """
    manage_models = [
        test_models.MixedTest,
        test_models.MixedRefTest,
    ]
    
    def test_merge_tags(self):
        tag_model = test_models.MixedTestTagModel
        
        # Set up database
        a1 = self.create(test_models.MixedTest, name='a1', singletag='one', tags='one')
        a2 = self.create(test_models.MixedTest, name='a2', singletag='two', tags='two')
        a3 = self.create(test_models.MixedTest, name='a3', singletag='three', tags='three')

        b1 = self.create(test_models.MixedRefTest, name='b1', singletag='one', tags='one')
        b2 = self.create(test_models.MixedRefTest, name='b2', singletag='two', tags='two')
        b3 = self.create(test_models.MixedRefTest, name='b3', singletag='three', tags='three')
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'one': 4,
            'two': 4,
            'three': 4,
        })
        self.assertInstanceEqual(a1, singletag='one', tags='one')
        self.assertInstanceEqual(a2, singletag='two', tags='two')
        self.assertInstanceEqual(a3, singletag='three', tags='three')
        self.assertInstanceEqual(b1, singletag='one', tags='one')
        self.assertInstanceEqual(b2, singletag='two', tags='two')
        self.assertInstanceEqual(b3, singletag='three', tags='three')
        
        # Merge tags
        s1 = tag_model.objects.get(name='one')
        s1.merge_tags(
            tag_model.objects.filter(name__in=['one', 'two', 'three'])
        )
        
        # Check it's correct
        self.assertTagModel(tag_model, {
            'one': 12,
        })
        self.assertInstanceEqual(a1, singletag='one', tags='one')
        self.assertInstanceEqual(a2, singletag='one', tags='one')
        self.assertInstanceEqual(a3, singletag='one', tags='one')
        self.assertInstanceEqual(b1, singletag='one', tags='one')
        self.assertInstanceEqual(b2, singletag='one', tags='one')
        self.assertInstanceEqual(b3, singletag='one', tags='one')

    def test_merge_multiple_tags(self):
        "Test merging a queryset of multiple tags"
        tag_model = test_models.MixedTestTagModel
        
        # Set up database
        t1 = self.create(test_models.MixedTest, name='Test 1', tags='blue, green, red')
        t2 = self.create(test_models.MixedTest, name='Test 2', tags='blue, green, red')
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'blue': 2,
            'green': 2,
            'red': 2,
        })
        self.assertInstanceEqual(t1, tags='blue, green, red')
        self.assertInstanceEqual(t2, tags='blue, green, red')
        
        # Merge tags
        s1 = tag_model.objects.get(name='blue')
        s1.merge_tags(
            tag_model.objects.filter(name__in=['blue', 'green', 'red'])
        )
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'blue': 2,
        })
        self.assertInstanceEqual(t1, tags='blue')
        self.assertInstanceEqual(t2, tags='blue')

    def test_merge_by_name(self):
        "Test merging a list of tag names, including tags which don't exist"
        tag_model = test_models.MixedTestTagModel
        
        # Set up database
        t1 = self.create(test_models.MixedTest, name='Test 1', tags='blue, green, red')
        t2 = self.create(test_models.MixedTest, name='Test 2', tags='blue, green, red')
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'blue': 2,
            'green': 2,
            'red': 2,
        })
        self.assertInstanceEqual(t1, tags='blue, green, red')
        self.assertInstanceEqual(t2, tags='blue, green, red')
        
        # Merge tags
        s1 = tag_model.objects.get(name='blue')
        s1.merge_tags(['blue', 'green', 'red', 'pink'])
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'blue': 2,
        })
        self.assertInstanceEqual(t1, tags='blue')
        self.assertInstanceEqual(t2, tags='blue')

    def test_merge_by_obj_list(self):
        "Test merging a list of tag objects"
        tag_model = test_models.MixedTestTagModel
        t1 = self.create(test_models.MixedTest, name='Test 1', tags='blue, green, red')
        t2 = self.create(test_models.MixedTest, name='Test 2', tags='blue, green, red')
        
        # Merge tags
        s1 = tag_model.objects.get(name='blue')
        s1.merge_tags(list(tag_model.objects.all()))
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'blue': 2,
        })
        self.assertInstanceEqual(t1, tags='blue')
        self.assertInstanceEqual(t2, tags='blue')

    def test_merge_by_tag_string(self):
        "Test merging a tag string, including tags which don't exist"
        tag_model = test_models.MixedTestTagModel
        t1 = self.create(test_models.MixedTest, name='Test 1', tags='blue, green, red')
        t2 = self.create(test_models.MixedTest, name='Test 2', tags='blue, green, red')
        
        # Merge tags
        s1 = tag_model.objects.get(name='blue')
        s1.merge_tags('blue, green, red, pink')
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'blue': 2,
        })
        self.assertInstanceEqual(t1, tags='blue')
        self.assertInstanceEqual(t2, tags='blue')


###############################################################################
####### Test tag model manager and queryset
###############################################################################

class TagModelQuerySetTest(TagTestManager, TestCase):
    """
    Test tag model queryset and manager
    """
    manage_models = [
        test_models.TagFieldOptionsModel,
    ]
    
    def setUpExtra(self):
        self.model = test_models.TagFieldOptionsModel
        self.tag_model = self.model.initial_list.tag_model
        self.o1 = self.model.objects.create(
            name='Test 1',
            initial_list='David, Eric',
        )
        self.o2 = self.model.objects.create(
            name='Test 2',
            initial_list='Eric, Frank',
        )
    
    def test_setup(self):
        self.assertTagModel(self.model.initial_list, {
            'Adam':  0,
            'Brian': 0,
            'Chris': 0,
            'David': 1,
            'Eric':  2,
            'Frank': 1,
        })
    
    def test_initial(self):
        initial_only = self.tag_model.objects.initial()
        self.assertEqual(len(initial_only), 3)
        self.assertEqual(initial_only[0], 'Adam')
        self.assertEqual(initial_only[1], 'Brian')
        self.assertEqual(initial_only[2], 'Chris')
    
    def test_filter_or_initial(self):
        filtered = self.tag_model.objects.filter_or_initial(
            tagfieldoptionsmodel__name='Test 1',
        )
        self.assertEqual(len(filtered), 5)
        self.assertEqual(filtered[0], 'Adam')
        self.assertEqual(filtered[1], 'Brian')
        self.assertEqual(filtered[2], 'Chris')
        self.assertEqual(filtered[3], 'David')
        self.assertEqual(filtered[4], 'Eric')
        
    def test_weight_scale_up(self):
        "Test weight() scales up to max"
        # Scale them to 2+2n: 0=2, 1=4, 2=6
        weighted = self.tag_model.objects.weight(min=2, max=6)
        self.assertEqual(len(weighted), 6)
        self.assertEqual(weighted[0].name, 'Adam')
        self.assertEqual(weighted[0].weight, 2)
        
        self.assertEqual(weighted[1], 'Brian')
        self.assertEqual(weighted[1].weight, 2)
        
        self.assertEqual(weighted[2], 'Chris')
        self.assertEqual(weighted[2].weight, 2)
        
        self.assertEqual(weighted[3], 'David')
        self.assertEqual(weighted[3].weight, 4)
        
        self.assertEqual(weighted[4], 'Eric')
        self.assertEqual(weighted[4].weight, 6)
        
        self.assertEqual(weighted[5], 'Frank')
        self.assertEqual(weighted[5].weight, 4)

    def test_weight_scale_down(self):
        "Test weight() scales down to max"
        # Add some extras so we can scale them 0.5n+2
        # Weight them so 0=2, 1=2 (rounded down), 4=4, 8=6
        
        # Eric will be used 8 times total - 6 more
        for i in range(6):
            self.model.objects.create(
                name='Test 3.%d' % i,
                initial_list='Eric',
            )
        
        # Frank will be used 4 times total - 3 more
        for i in range(3):
            self.model.objects.create(
                name='Test 4.%d' % i,
                initial_list='Frank',
            )
        
        self.assertTagModel(self.model.initial_list, {
            'Adam':  0,
            'Brian': 0,
            'Chris': 0,
            'David': 1,
            'Eric':  8,
            'Frank': 4,
        })
        
        weighted = self.tag_model.objects.weight(min=2, max=6)
        self.assertEqual(len(weighted), 6)
        self.assertEqual(weighted[0].name, 'Adam')
        self.assertEqual(weighted[0].weight, 2)
        
        self.assertEqual(weighted[1], 'Brian')
        self.assertEqual(weighted[1].weight, 2)
        
        self.assertEqual(weighted[2], 'Chris')
        self.assertEqual(weighted[2].weight, 2)
        
        self.assertEqual(weighted[3], 'David')
        self.assertEqual(weighted[3].weight, 2)
        
        self.assertEqual(weighted[4], 'Eric')
        self.assertEqual(weighted[4].weight, 6)
        
        self.assertEqual(weighted[5], 'Frank')
        self.assertEqual(weighted[5].weight, 4)
    
    def test_to_string(self):
        "Check manager and queryset can be converted to a tag string"
        self.assertEqual(
            six.text_type(self.tag_model.objects),
            'Adam, Brian, Chris, David, Eric, Frank',
        )
        self.assertEqual(
            six.text_type(self.tag_model.objects.all()),
            'Adam, Brian, Chris, David, Eric, Frank',
        )
        self.assertEqual(
            six.text_type(self.tag_model.objects.initial()),
            'Adam, Brian, Chris',
        )
        self.assertEqual(
            six.text_type(self.o1.initial_list),
            'David, Eric',
        )
