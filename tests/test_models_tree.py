"""
Tagulous test: Tag Trees

Modules tested:
    tagulous.models.tree
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from tests.lib import *


class TagTreeTestManager(TagTestManager):
    """
    Manage tag tree tests
    """
    def assertTreeTag(
        self, tag, name=None, label=None, slug=None, path=None,
        parent=None, count=None, protected=None, level=None,
    ):
        "Check tag attributes match those specified"
        if name is not None:
            self.assertEqual(tag.name, name)
        if label is not None:
            self.assertEqual(tag.label, label)
        if slug is not None:
            self.assertEqual(tag.slug, slug)
        if path is not None:
            self.assertEqual(tag.path, path)
        
        if parent is not None:
            self.assertEqual(tag.parent, parent)
        if count is not None:
            self.assertEqual(tag.count, count)
        if protected is not None:
            self.assertEqual(tag.protected, protected)
        if level is not None:
            self.assertEqual(tag.level, level)
            

###############################################################################
####### TagTreeModel basics
###############################################################################

class TagTreeModelTest(TagTreeTestManager, TestCase):
    """
    Test TagTreeModel basics - that the models are created correctly, and tag
    instances can be created directly with parents and fields correct.
    
    These tests refer to levels; the higher the level, the deeper in the tree,
    eg: level1/level2/level3
    """
    manage_models = [
        test_models.TreeTest,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.TreeTest
        self.singletag_field = test_models.TreeTest.singletag
        self.singletag_model = test_models.TreeTest.singletag.tag_model
        self.tag_field = test_models.TreeTest.tags
        self.tag_model = test_models.TreeTest.tags.tag_model
    
    def test_singletag_model(self):
        "Check tag tree model is used as a base when SingleTagField tree=True"
        self.assertTrue(issubclass(
            self.singletag_model, tag_models.TagTreeModel
        ))
        
    def test_tag_model(self):
        "Check tag tree model is used as a base when TagField tree=True"
        self.assertTrue(issubclass(
            self.tag_model, tag_models.TagTreeModel
        ))

    def test_level_1(self):
        "Check level 1 node created correctly"
        t1 = self.tag_model.objects.create(name='One')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', level=1,
        )
    
    def test_level_2_existing_l1(self):
        "Check level 2 node created with existing level 1"
        t1 = self.tag_model.objects.create(name='One')
        t2 = self.tag_model.objects.create(name='One/Two')
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, level=2,
        )

    def test_level_2_missing_l1(self):
        "Check level 2 node creates missing level 1"
        t2 = self.tag_model.objects.create(name='One/Two')
        t1 = self.tag_model.objects.get(name='One')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', level=1,
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, level=2,
        )
    
    def test_level_3_existing_l1_l2(self):
        "Check level 3 node created with existing level 1 and 2"
        t1 = self.tag_model.objects.create(name='One')
        t2 = self.tag_model.objects.create(name='One/Two')
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, level=3,
        )
        
    def test_level_3_existing_l1_missing_l2(self):
        "Check level 3 node created with existing level 1 but missing level 2"
        t1 = self.tag_model.objects.create(name='One')
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        t2 = self.tag_model.objects.get(name='One/Two')
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, level=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, level=3,
        )
    
    def test_level_3_missing_l1_l2(self):
        "Check level 3 node created with missing level 1 and 2"
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        t1 = self.tag_model.objects.get(name='One')
        t2 = self.tag_model.objects.get(name='One/Two')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', level=1,
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, level=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, level=3,
        )
    
    def test_level_1_renames_l2_l3(self):
        "Check renaming level 1 node renames l2 and l3"
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        t1 = self.tag_model.objects.get(name='One')
        self.assertTagModel(self.tag_model, {
            'One': 0,
            'One/Two': 0,
            'One/Two/Three': 0,
        })
        t1.name = 'Uno'
        t1.slug = None # Force slug to be recreated
        t1.save()
        
        # Reload
        self.assertTagModel(self.tag_model, {
            'Uno': 0,
            'Uno/Two': 0,
            'Uno/Two/Three': 0,
        })
        t1 = self.tag_model.objects.get(name='Uno')
        t2 = self.tag_model.objects.get(name='Uno/Two')
        t3 = self.tag_model.objects.get(name='Uno/Two/Three')
        
        self.assertTreeTag(
            t1, name='Uno', label='Uno', slug='uno', path='uno', level=1,
        )
        self.assertTreeTag(
            t2, name='Uno/Two', label='Two', slug='two', path='uno/two',
            parent=t1, level=2,
        )
        self.assertTreeTag(
            t3, name='Uno/Two/Three', label='Three',
            slug='three', path='uno/two/three',
            parent=t2, level=3,
        )

    def test_rebuild(self):
        "Check rebuild updates all slugs"
        # Break slugs
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        for tag in self.tag_model.objects.all():
            tag.slug = six.text_type(tag.pk)
            tag.save()
        
        # Load
        t1 = self.tag_model.objects.get(name='One')
        t2 = self.tag_model.objects.get(name='One/Two')
        t3 = self.tag_model.objects.get(name='One/Two/Three')
        self.assertTreeTag(t1, name='One', slug='1', path='1')
        self.assertTreeTag(t2, name='One/Two', slug='2', path='1/2', parent=t1)
        self.assertTreeTag(
            t3, name='One/Two/Three', slug='3', path='1/2/3', parent=t2
        )
        
        # Rebuild and re-test
        self.tag_model.objects.rebuild()
        t1 = self.tag_model.objects.get(name='One')
        t2 = self.tag_model.objects.get(name='One/Two')
        t3 = self.tag_model.objects.get(name='One/Two/Three')
        self.assertTreeTag(t1, name='One', slug='one', path='one')
        self.assertTreeTag(
            t2, name='One/Two', slug='two', path='one/two', parent=t1,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', slug='three', path='one/two/three',
            parent=t2,
        )
        

###############################################################################
####### TagTreeModel tree merging
###############################################################################

class TagTreeModelMergeTest(TagTreeTestManager, TestCase):
    """
    Test merging TagTreeModel nodes
    """
    manage_models = [
        test_models.TreeTest,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.TreeTest
        self.tag_field = test_models.TreeTest.tags
        self.tag_model = test_models.TreeTest.tags.tag_model
        
        # Normal Animal leaf nodes
        self.test_model.objects.create(name='cat1', tags='Animal/Mammal/Cat')
        self.test_model.objects.create(name='dog1', tags='Animal/Mammal/Dog')
        self.test_model.objects.create(name='bee1', tags='Animal/Insect/Bee')
        
        # Pet tree has Cat leaf and extra L2 not in Animal
        self.test_model.objects.create(name='cat2', tags='Pet/Mammal/Cat')
        self.test_model.objects.create(name='robin1', tags='Pet/Bird/Robin')
        
        # Food tree has Cat leaf and extra L3 not in Animal
        self.test_model.objects.create(name='cat3', tags='Food/Mammal/Cat')
        self.test_model.objects.create(name='pig1', tags='Food/Mammal/Pig')
    
    def test_setup(self):
        "Check test setup is correct"
        # There should be 6 tags
        self.assertTagModel(self.tag_model, {
            'Animal':               0,
            'Animal/Insect':        0,
            'Animal/Insect/Bee':    1,
            'Animal/Mammal':        0,
            'Animal/Mammal/Cat':    1,
            'Animal/Mammal/Dog':    1,
            'Pet':                  0,
            'Pet/Mammal':           0,
            'Pet/Mammal/Cat':       1,
            'Pet/Bird':             0,
            'Pet/Bird/Robin':       1,
            'Food':                 0,
            'Food/Mammal':          0,
            'Food/Mammal/Cat':      1,
            'Food/Mammal/Pig':      1,
        })
    
    def test_merge_l1(self):
        """
        Test that merging an l1 without merging children reassigns tagged
        items, but leaves self and children
        """
        # Tag something with 'Pet'
        t1 = self.test_model.objects.create(name='pet1', tags='Pet')
        self.assertEqual(
            self.tag_model.objects.get(name='Pet').count, 1,
        )
        
        # Now merge
        self.tag_model.objects.get(name='Animal').merge_tags(
            'Pet, Food', children=False,
        )
        self.assertTagModel(self.tag_model, {
            'Animal':               1,
            'Animal/Insect':        0,
            'Animal/Insect/Bee':    1,
            'Animal/Mammal':        0,
            'Animal/Mammal/Cat':    1,
            'Animal/Mammal/Dog':    1,
            'Pet':                  0,
            'Pet/Mammal':           0,
            'Pet/Mammal/Cat':       1,
            'Pet/Bird':             0,
            'Pet/Bird/Robin':       1,
            'Food':                 0,
            'Food/Mammal':          0,
            'Food/Mammal/Cat':      1,
            'Food/Mammal/Pig':      1,
        })
        self.assertInstanceEqual(t1, name='pet1', tags='Animal')
        
    def test_merge_l1_with_children(self):
        """
        Test that merging an l1 and its children merges the full subtrees and
        cleans empty parents
        """
        # Now merge
        self.tag_model.objects.get(name='Animal').merge_tags(
            'Pet, Food', children=True,
        )
        self.assertTagModel(self.tag_model, {
            'Animal':               0,
            'Animal/Insect':        0,
            'Animal/Insect/Bee':    1,
            'Animal/Mammal':        0,
            'Animal/Mammal/Cat':    3,
            'Animal/Mammal/Dog':    1,
            'Animal/Mammal/Pig':    1,
            'Animal/Bird':          0,
            'Animal/Bird/Robin':    1,
        })
    
    def test_merge_l2(self):
        """
        Test that merging an l2 without merging children reassigns tagged
        items, but leaves self and children
        """
        # Tag something with 'Pet/Mammal'
        t1 = self.test_model.objects.create(name='mammal1', tags='Pet/Mammal')
        self.assertEqual(
            self.tag_model.objects.get(name='Pet/Mammal').count, 1,
        )
        
        # Now merge
        self.tag_model.objects.get(name='Animal/Mammal').merge_tags(
            'Pet/Mammal, Food/Mammal', children=False,
        )
        self.assertTagModel(self.tag_model, {
            'Animal':               0,
            'Animal/Insect':        0,
            'Animal/Insect/Bee':    1,
            'Animal/Mammal':        1,
            'Animal/Mammal/Cat':    1,
            'Animal/Mammal/Dog':    1,
            'Pet':                  0,
            'Pet/Mammal':           0,
            'Pet/Mammal/Cat':       1,
            'Pet/Bird':             0,
            'Pet/Bird/Robin':       1,
            'Food':                 0,
            'Food/Mammal':          0,
            'Food/Mammal/Cat':      1,
            'Food/Mammal/Pig':      1,
        })
        self.assertInstanceEqual(t1, name='mammal1', tags='Animal/Mammal')
    
    def test_merge_l2_with_children(self):
        """
        Test that merging an l2 and its children merges the full subtrees and
        cleans empty parents
        """
        # Now merge
        self.tag_model.objects.get(name='Animal/Mammal').merge_tags(
            'Pet/Mammal, Food/Mammal', children=True,
        )
        self.assertTagModel(self.tag_model, {
            'Animal':               0,
            'Animal/Insect':        0,
            'Animal/Insect/Bee':    1,
            'Animal/Mammal':        0,
            'Animal/Mammal/Cat':    3,
            'Animal/Mammal/Dog':    1,
            'Animal/Mammal/Pig':    1,
            'Pet':                  0,
            'Pet/Bird':             0,
            'Pet/Bird/Robin':       1,
        })
    
    def test_merge_l3(self):
        "Test merging an l3 cleans empty parents"
        # No need to test children=True - there are no children
        self.tag_model.objects.get(name='Animal/Mammal/Cat').merge_tags(
            'Pet/Mammal/Cat, Food/Mammal/Cat', children=False,
        )
        self.assertTagModel(self.tag_model, {
            'Animal':               0,
            'Animal/Insect':        0,
            'Animal/Insect/Bee':    1,
            'Animal/Mammal':        0,
            'Animal/Mammal/Cat':    3,
            'Animal/Mammal/Dog':    1,
            'Pet':                  0,
            # Pet/Mammal now empty
            'Pet/Bird':             0,
            'Pet/Bird/Robin':       1,
            'Food':                 0,
            'Food/Mammal':          0,
            'Food/Mammal/Pig':      1,
        })
        

###############################################################################
####### Custom TagTreeModel basics
###############################################################################

class TagTreeModelCustomTest(TagTreeTestManager, TransactionTestCase):
    """
    Test TagTreeModel basics when using a custom model
    
    Use a TransactionTestCase so the apps will be reset
    """
    manage_models = [
        test_models.CustomTreeTest,
    ]
    
    def setUpExtra(self):
        self.test_model = test_models.CustomTreeTest
        self.tag_model = test_models.CustomTagTree
        self.singletag_field = test_models.CustomTreeTest.singletag
        self.tag_field = test_models.CustomTreeTest.tags
    
    def test_tag_model(self):
        "Check tag tree model is used as a base"
        self.assertTrue(issubclass(
            self.tag_model, tag_models.TagTreeModel
        ))
        
    def test_tree_option(self):
        "Check tag tree model forces tree=True when missing"
        self.assertTrue(self.tag_model.tag_options.tree)
        self.assertTrue(self.singletag_field.tag_options.tree)
        self.assertTrue(self.tag_field.tag_options.tree)
        
    def test_tree_option_tagmodel_fail(self):
        "Check tree option is not allowed in TagMeta"
        with self.assertRaises(ValueError) as cm:
            class FailModel_tree_tagmeta(tag_models.TagModel):
                class TagMeta:
                    tree = True
        self.assertEqual(
            six.text_type(cm.exception),
            "Cannot set tree option in TagMeta"
        )
    

###############################################################################
####### TagTreeModel tree navigation methods
###############################################################################

class TagTreeModelNavTest(TagTreeTestManager, TestCase):
    """
    Test navigation through TagTreeModel - get_ancestors etc
    """
    manage_models = [
        test_models.TreeTest,
    ]
    
    def setUpExtra(self):
        self.tag_field = test_models.TreeTest.tags
        self.tag_model = test_models.TreeTest.tags.tag_model
        
        self.cat = self.tag_model.objects.create(name='Animal/Mammal/Cat')
        self.dog = self.tag_model.objects.create(name='Animal/Mammal/Dog')
        self.bee = self.tag_model.objects.create(name='Animal/Insect/Bee')
        
    def test_setup(self):
        "Check test setup is correct"
        # There should be 6 tags
        self.assertTagModel(self.tag_model, {
            'Animal': 0,
            'Animal/Insect': 0,
            'Animal/Insect/Bee': 0,
            'Animal/Mammal': 0,
            'Animal/Mammal/Cat': 0,
            'Animal/Mammal/Dog': 0,
        })
        
    def test_ancestors(self):
        "Check l1 and l2 ancestors found from l3"
        # Add in some more extras to make sure they're not picked up
        f1 = self.tag_model.objects.create(name='Fail')
        f2 = self.tag_model.objects.create(name='Animal/Fail')
        f3 = self.tag_model.objects.create(name='Animal/Mammal/Cat/Fail')
        
        # Look up from Cat
        t1 = self.tag_model.objects.get(name='Animal/Mammal/Cat')
        anc = t1.get_ancestors()
        self.assertEqual(len(anc), 2)
        self.assertTreeTag(anc[0], name='Animal', level=1)
        self.assertTreeTag(anc[1], name='Animal/Mammal', level=2)
        
    def test_no_ancestors(self):
        "Check no ancestors found from l1"
        t1 = self.tag_model.objects.get(name='Animal')
        self.assertEqual(len(t1.get_ancestors()), 0)
        
    def test_descendants_l1(self):
        "Check l2 and l3 descendants found from l1"
        # Add in some extras to make sure they're not picked up
        f1 = self.tag_model.objects.create(name='Fail')
        
        # Look down from Animal
        t1 = self.tag_model.objects.get(name='Animal')
        self.assertTreeTag(t1, name='Animal', level=1)
        dec = t1.get_descendants()
        self.assertEqual(len(dec), 5)
        self.assertTreeTag(dec[0], name='Animal/Insect', level=2)
        self.assertTreeTag(dec[1], name='Animal/Insect/Bee', level=3)
        self.assertTreeTag(dec[2], name='Animal/Mammal', level=2)
        self.assertTreeTag(dec[3], name='Animal/Mammal/Cat', level=3)
        self.assertTreeTag(dec[4], name='Animal/Mammal/Dog', level=3)
        
    def test_descendants_l2(self):
        "Check l3 descendants found from l2"
        # Look down from Animal
        t1 = self.tag_model.objects.get(name='Animal/Mammal')
        self.assertTreeTag(t1, name='Animal/Mammal', level=2)
        dec = t1.get_descendants()
        self.assertEqual(len(dec), 2)
        self.assertTreeTag(dec[0], name='Animal/Mammal/Cat', level=3)
        self.assertTreeTag(dec[1], name='Animal/Mammal/Dog', level=3)

    def test_descendants_l2(self):
        "Check no descendants found from l3"
        # Look down from Animal
        t1 = self.tag_model.objects.get(name='Animal/Insect/Bee')
        self.assertTreeTag(t1, name='Animal/Insect/Bee', level=3)
        dec = t1.get_descendants()
        self.assertEqual(len(dec), 0)
    
    def test_siblings_l1(self):
        "Find level 1 siblings"
        # Add another level 1 tag to find
        l1_2 = self.tag_model.objects.create(name='Vegetable')
        
        t1 = self.tag_model.objects.get(name='Animal')
        sibs = t1.get_siblings()
        self.assertEqual(len(sibs), 2)
        self.assertTreeTag(sibs[0], name='Animal', level=1)
        self.assertTreeTag(sibs[1], name='Vegetable', level=1)
        
    def test_siblings_l2(self):
        "Find level 2 siblings"
        t1 = self.tag_model.objects.get(name='Animal/Insect')
        sibs = t1.get_siblings()
        self.assertEqual(len(sibs), 2)
        self.assertTreeTag(sibs[0], name='Animal/Insect', level=2)
        self.assertTreeTag(sibs[1], name='Animal/Mammal', level=2)
    
    
###############################################################################
####### TagTreeQuerySet
###############################################################################

class TagTreeQuerySetTest(TagTreeTestManager, TestCase):
    """
    Test navigation using TagTreeModelQuerySet
    """
    manage_models = [
        test_models.TreeTest,
    ]
    
    def setUpExtra(self):
        self.tag_field = test_models.TreeTest.tags
        self.tag_model = test_models.TreeTest.tags.tag_model
        
        self.cat = self.tag_model.objects.create(name='Animal/Mammal/Cat')
        self.dog = self.tag_model.objects.create(name='Animal/Mammal/Dog')
        self.bee = self.tag_model.objects.create(name='Animal/Insect/Bee')
        self.vegetable = self.tag_model.objects.create(name='Vegetable')
        
    def test_setup(self):
        "Check test setup is correct"
        # There should be 6 tags
        self.assertTagModel(self.tag_model, {
            'Animal': 0,
            'Animal/Insect': 0,
            'Animal/Insect/Bee': 0,
            'Animal/Mammal': 0,
            'Animal/Mammal/Cat': 0,
            'Animal/Mammal/Dog': 0,
            'Vegetable': 0,
        })
    
    def test_ancestors_l1(self):
        qs = self.tag_model.objects.filter(level=1)
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Animal', 'Vegetable',
        ])
        
        qs = qs.with_ancestors()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal', 'Vegetable',
        ])

    def test_ancestors_l2(self):
        qs = self.tag_model.objects.filter(level=2)
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Insect', 'Mammal',
        ])
        
        qs = qs.with_ancestors()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal',
            'Animal/Insect',
            'Animal/Mammal',
        ])
        
    def test_ancestors_l3(self):
        qs = self.tag_model.objects.filter(level=3)
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Bee', 'Cat', 'Dog',
        ])
        
        qs = qs.with_ancestors()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal',
            'Animal/Insect',
            'Animal/Insect/Bee',
            'Animal/Mammal',
            'Animal/Mammal/Cat',
            'Animal/Mammal/Dog',
        ])
    
    def test_descendants_l1(self):
        qs = self.tag_model.objects.filter(level=1)
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Animal', 'Vegetable',
        ])
        
        qs = qs.with_descendants()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal',
            'Animal/Insect',
            'Animal/Insect/Bee',
            'Animal/Mammal',
            'Animal/Mammal/Cat',
            'Animal/Mammal/Dog',
            'Vegetable',
        ])
    
    def test_descendants_l2(self):
        qs = self.tag_model.objects.filter(level=2)
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Insect', 'Mammal',
        ])
        
        qs = qs.with_descendants()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal/Insect',
            'Animal/Insect/Bee',
            'Animal/Mammal',
            'Animal/Mammal/Cat',
            'Animal/Mammal/Dog',
        ])
    
    def test_descendants_l3(self):
        qs = self.tag_model.objects.filter(level=3)
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Bee', 'Cat', 'Dog',
        ])
        
        qs = qs.with_descendants()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal/Insect/Bee',
            'Animal/Mammal/Cat',
            'Animal/Mammal/Dog',
        ])
    
    def test_siblings_l1(self):
        qs = self.tag_model.objects.filter(name='Animal')
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Animal',
        ])
        
        qs = qs.with_siblings()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal', 'Vegetable',
        ])

    def test_siblings_l2(self):
        # Throw in something else to ensure l2 stays within subtree
        f1 = self.tag_model.objects.create(name='Vegetable/Horrible')
        
        qs = self.tag_model.objects.filter(name='Animal/Insect')
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Insect',
        ])
        
        qs = qs.with_siblings()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal/Insect',
            'Animal/Mammal',
        ])
        
    def test_siblings_l3(self):
        # Throw in something else to ensure l3 stays within subtree
        f1 = self.tag_model.objects.create(name='Vegetable/Horrible/Mushroom')
        
        qs = self.tag_model.objects.filter(name='Animal/Mammal/Cat')
        self.assertSequenceEqual(qs.values_list('label', flat=True), [
            'Cat',
        ])
        
        qs = qs.with_siblings()
        self.assertSequenceEqual(qs.values_list('name', flat=True), [
            'Animal/Mammal/Cat',
            'Animal/Mammal/Dog',
        ])
        


###############################################################################
####### TagTreeModel access via fields
###############################################################################

class TagTreeModelFieldTest(TagTreeTestManager, TestCase):
    """
    Test TagTreeModel access via fields - creation and deletion
    """
    manage_models = [
        test_models.TreeTest,
    ]
    
    def setUpExtra(self):
        self.singletag_field = test_models.TreeTest.singletag
        self.singletag_model = test_models.TreeTest.singletag.tag_model
        self.tag_field = test_models.TreeTest.tags
        self.tag_model = test_models.TreeTest.tags.tag_model
    

    def test_singletagfield_level_3(self):
        """
        Check level 3 nodes created with missing level 1 and 2 when assigned
        via singletag fields
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            singletag='One/Two/Three',
        )
        t1 = self.singletag_model.objects.get(name='One')
        t2 = self.singletag_model.objects.get(name='One/Two')
        t3 = self.singletag_model.objects.get(name='One/Two/Three')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', level=1,
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, level=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, count=1, level=3,
        )
        
        self.assertTagModel(self.singletag_model, {
            'One': 0,
            'One/Two': 0,
            'One/Two/Three': 1,
        })
        self.assertTagModel(self.tag_model, {})
    
    def test_tagfield_level_3(self):
        """
        Check level 3 nodes created with missing level 1 and 2 when assigned
        via tag fields
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            tags='One/Two/Three, Uno/Dos/Tres',
        )
        
        self.assertTagModel(self.singletag_model, {})
        self.assertTagModel(self.tag_model, {
            'One': 0,
            'One/Two': 0,
            'One/Two/Three': 1,
            'Uno': 0,
            'Uno/Dos': 0,
            'Uno/Dos/Tres': 1,
        })
        
        t1 = self.tag_model.objects.get(name='One')
        t2 = self.tag_model.objects.get(name='One/Two')
        t3 = self.tag_model.objects.get(name='One/Two/Three')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', level=1
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, level=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, level=3, count=1,
        )


    def test_delete_l2_empty_l1(self):
        """
        Check deleting a level 2 node cleans away empty level 1
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            singletag='One/Two',
        )
        self.assertTagModel(self.singletag_model, {
            'One': 0,
            'One/Two': 1,
        })
        
        obj1.singletag = ''
        obj1.save()
        self.assertTagModel(self.singletag_model, {})
    
    def test_delete_l2_populated_l1(self):
        """
        Check deleting a level 2 node leaves a populated l1
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            singletag='Uno/Dos',
        )
        t2 = self.singletag_model.objects.create(name='Uno/Due')
        self.assertTagModel(self.singletag_model, {
            'Uno': 0,
            'Uno/Dos': 1,
            'Uno/Due': 0,
        })
        
        obj1.singletag = ''
        obj1.save()
        self.assertTagModel(self.singletag_model, {
            'Uno': 0,
            'Uno/Due': 0,
        })

    def test_delete_l3_populated_l2(self):
        """
        Check deleting a level 3 node leaves a populated level 2
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            singletag='No/Uno/Dos',
        )
        t2 = self.singletag_model.objects.create(name='No/Uno/Due')
        self.assertTagModel(self.singletag_model, {
            'No': 0,
            'No/Uno': 0,
            'No/Uno/Dos': 1,
            'No/Uno/Due': 0,
        })
        
        obj1.singletag = ''
        obj1.save()
        self.assertTagModel(self.singletag_model, {
            'No': 0,
            'No/Uno': 0,
            'No/Uno/Due': 0,
        })

    def test_delete_l3_empty_l2_populated_l1(self):
        """
        Check deleting a level 3 node cleans empty l2 but leaves populated l1
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            singletag='Uno/Dos/Tres',
        )
        t2 = self.singletag_model.objects.create(name='Uno/Due/Tre')
        self.assertTagModel(self.singletag_model, {
            'Uno': 0,
            'Uno/Dos': 0,
            'Uno/Dos/Tres': 1,
            'Uno/Due': 0,
            'Uno/Due/Tre': 0,
        })
        
        obj1.singletag = ''
        obj1.save()
        self.assertTagModel(self.singletag_model, {
            'Uno': 0,
            'Uno/Due': 0,
            'Uno/Due/Tre': 0,
        })

    def test_delete_l3_used_l2(self):
        """
        Check deleting a level 3 node leaves an empty but used level 2
        """
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1',
            singletag='Uno/Dos',
        )
        obj2 = test_models.TreeTest.objects.create(
            name='Test 2',
            singletag='Uno/Dos/Tres',
        )
        self.assertTagModel(self.singletag_model, {
            'Uno': 0,
            'Uno/Dos': 1,
            'Uno/Dos/Tres': 1,
        })
        
        obj2.singletag = ''
        obj2.save()
        self.assertTagModel(self.singletag_model, {
            'Uno': 0,
            'Uno/Dos': 1,
        })

    def test_delete_l1_used_l2(self):
        "Check deleting a level 1 node with used level 2 leaves both"
        obj1 = test_models.TreeTest.objects.create(
            name='Test 1', singletag='one',
        )
        obj2 = test_models.TreeTest.objects.create(
            name='Test 2', singletag='one/two',
        )
        
        self.assertTagModel(self.singletag_model, {
            'one': 1,
            'one/two': 1,
        })
        obj1.singletag=''
        obj1.save()
        self.assertTagModel(self.singletag_model, {
            'one': 0,
            'one/two': 1,
        })

    def test_get_descendant_count(self):
        "Check the count of the descendants"
        # Make four of everything
        for i in range(4):
            test_models.TreeTest.objects.create(
                name='Test 1.%d' % i, singletag='One',
            )
            test_models.TreeTest.objects.create(
                name='Test 2.%d' % i, singletag='One/Two',
            )
            test_models.TreeTest.objects.create(
                name='Test 3.%d' % i, singletag='One/Two/Three',
            )
        self.assertTagModel(self.singletag_model, {
            'One': 4,
            'One/Two': 4,
            'One/Two/Three': 4,
        })
        
        # Check the counts
        t1 = self.singletag_model.objects.get(name='One')
        t2 = self.singletag_model.objects.get(name='One/Two')
        t3 = self.singletag_model.objects.get(name='One/Two/Three')
        self.assertEqual(t1.descendant_count, 8)
        self.assertEqual(t2.descendant_count, 4)
        self.assertEqual(t3.descendant_count, 0)

    def test_get_family_count(self):
        "Check the count of the family - node plus descendants"
        # Make four of everything
        for i in range(4):
            test_models.TreeTest.objects.create(
                name='Test 1.%d' % i, singletag='One',
            )
            test_models.TreeTest.objects.create(
                name='Test 2.%d' % i, singletag='One/Two',
            )
            test_models.TreeTest.objects.create(
                name='Test 3.%d' % i, singletag='One/Two/Three',
            )
        self.assertTagModel(self.singletag_model, {
            'One': 4,
            'One/Two': 4,
            'One/Two/Three': 4,
        })
        
        # Check the counts
        t1 = self.singletag_model.objects.get(name='One')
        t2 = self.singletag_model.objects.get(name='One/Two')
        t3 = self.singletag_model.objects.get(name='One/Two/Three')
        self.assertEqual(t1.family_count, 12)
        self.assertEqual(t2.family_count, 8)
        self.assertEqual(t3.family_count, 4)
