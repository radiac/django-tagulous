"""
Tagulous test: Tag models

Modules tested:
    tagulous.models.models.BaseTagModel
    tagulous.models.models.TagModel
"""
from tagulous.tests.lib import *


class TagModelTest(TagTestManager, TestCase):
    """
    Test tag model
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
        t1a = self.tag_model.objects.create(name='one')
        t1b = self.tag_model.objects.get(name='one')
        self.assertEqual(t1a, t1b)

    def test_tags_equal_string(self):
        t1 = self.tag_model.objects.create(name='one')
        self.assertEqual(t1, 'one')

    def test_tags_not_equal_instance(self):
        t1 = self.tag_model.objects.create(name='one')
        t2 = self.tag_model.objects.create(name='two')
        self.assertNotEqual(t1, t2)

    def test_tags_not_equal_string(self):
        t1 = self.tag_model.objects.create(name='one')
        self.assertNotEqual(t1, 'two')
    
    def test_get_related_fields(self):
        "Check the class method returns a list of related fields"
        related_fields = self.tag_model.get_related_fields()
        self.assertEqual(len(related_fields), 4)
        
        # FK comes before M2M, so first two will be the SingleTagFields
        # Should be safe to assume order of models
        self.assertEqual(related_fields[0].model, self.model1)
        self.assertEqual(related_fields[1].model, self.model2)
        self.assertEqual(
            related_fields[0].field,
            test_models.MixedTest._meta.get_field('singletag')
        )
        self.assertEqual(
            related_fields[1].field,
            test_models.MixedRefTest._meta.get_field('singletag')
        )
        
        # Now the TagFields
        self.assertEqual(related_fields[2].model, self.model1)
        self.assertEqual(related_fields[3].model, self.model2)
        self.assertEqual(
            related_fields[2].field,
            test_models.MixedTest._meta.get_field('tags')
        )
        self.assertEqual(
            related_fields[3].field,
            test_models.MixedRefTest._meta.get_field('tags')
        )
        
    def test_get_related_fields_standard(self):
        "Check the class method can also find standard relationships"
        related_fields = self.tag_model.get_related_fields(include_standard=True)
        self.assertEqual(len(related_fields), 6)
        
        # SingleTagFields/FKs - don't bother re-testing singletagfields
        self.assertEqual(related_fields[0].model, self.model1)
        self.assertEqual(related_fields[1].model, self.model2)
        self.assertEqual(related_fields[2].model, self.model_nontag)
        self.assertEqual(
            related_fields[2].field,
            self.model_nontag._meta.get_field('fk')
        )
        
        # TagFields/M2Ms - don't bother re-testing tagfields
        self.assertEqual(related_fields[3].model, self.model1)
        self.assertEqual(related_fields[4].model, self.model2)
        self.assertEqual(related_fields[5].model, self.model_nontag)
        self.assertEqual(
            related_fields[5].field,
            self.model_nontag._meta.get_field('mm')
        )
        
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
        rel_st1.sort(cmp=lambda x, y: cmp(x.name, y.name))
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
        rel_t2.sort(cmp=lambda x, y: cmp(x.name, y.name))
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
        rel_t1.sort(cmp=lambda x, y: cmp(x.name, y.name))
        self.assertEqual(rel_t1[0], t1)
        self.assertEqual(rel_t1[1], t2)
        self.assertEqual(rel_t1[2], t2)
        
        # Check blue distinct
        rel_t2 = tags1.get_related_objects(flat=True, distinct=True)
        self.assertEqual(len(rel_t2), 2)
        rel_t2.sort(cmp=lambda x, y: cmp(x.name, y.name))
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
        rel_st1.sort(cmp=lambda x, y: cmp(x.name, y.name))
        self.assertEqual(rel_st1[0], t1)
        self.assertEqual(rel_st1[1], t2)
        
        # Check blue
        rel_t1 = tags1.get_related_objects(flat=True, include_standard=True)
        self.assertEqual(len(rel_t1), 2)
        rel_t1.sort(cmp=lambda x, y: cmp(x.name, y.name))
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
        