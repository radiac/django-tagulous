"""
Tagulous test: Tag Trees

Modules tested:
    tagulous.models.tree
"""
from tagulous.tests.lib import *


class TagTreeTestManager(TagTestManager):
    """
    Manage tag tree tests
    """
    def assertTreeTag(
        self, tag, name=None, label=None, slug=None, path=None,
        parent=None, count=None, protected=None, depth=None,
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
        if depth is not None:
            self.assertEqual(tag.depth, depth)
            

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
            t1, name='One', label='One', slug='one', path='one', depth=1,
        )
    
    def test_level_2_existing_l1(self):
        "Check level 2 node created with existing level 1"
        t1 = self.tag_model.objects.create(name='One')
        t2 = self.tag_model.objects.create(name='One/Two')
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, depth=2,
        )

    def test_level_2_missing_l1(self):
        "Check level 2 node creates missing level 1"
        t2 = self.tag_model.objects.create(name='One/Two')
        t1 = self.tag_model.objects.get(name='One')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', depth=1,
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, depth=2,
        )
    
    def test_level_3_existing_l1_l2(self):
        "Check level 3 node created with existing level 1 and 2"
        t1 = self.tag_model.objects.create(name='One')
        t2 = self.tag_model.objects.create(name='One/Two')
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, depth=3,
        )
        
    def test_level_3_existing_l1_missing_l2(self):
        "Check level 3 node created with existing level 1 but missing level 2"
        t1 = self.tag_model.objects.create(name='One')
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        t2 = self.tag_model.objects.get(name='One/Two')
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, depth=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, depth=3,
        )
    
    def test_level_3_missing_l1_l2(self):
        "Check level 3 node created with missing level 1 and 2"
        t3 = self.tag_model.objects.create(name='One/Two/Three')
        t1 = self.tag_model.objects.get(name='One')
        t2 = self.tag_model.objects.get(name='One/Two')
        self.assertTreeTag(
            t1, name='One', label='One', slug='one', path='one', depth=1,
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, depth=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, depth=3,
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
            t1, name='Uno', label='Uno', slug='uno', path='uno', depth=1,
        )
        self.assertTreeTag(
            t2, name='Uno/Two', label='Two', slug='two', path='uno/two',
            parent=t1, depth=2,
        )
        self.assertTreeTag(
            t3, name='Uno/Two/Three', label='Three',
            slug='three', path='uno/two/three',
            parent=t2, depth=3,
        )


class TagTreeModelNavTest(TagTreeTestManager, TestCase):
    """
    Test navigation through TagTreeModel - get_ancestors and get_descendants
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
        self.assertTreeTag(anc[0], name='Animal', depth=1)
        self.assertTreeTag(anc[1], name='Animal/Mammal', depth=2)
        
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
        self.assertTreeTag(t1, name='Animal', depth=1)
        dec = t1.get_descendants()
        self.assertEqual(len(dec), 5)
        self.assertTreeTag(dec[0], name='Animal/Insect', depth=2)
        self.assertTreeTag(dec[1], name='Animal/Insect/Bee', depth=3)
        self.assertTreeTag(dec[2], name='Animal/Mammal', depth=2)
        self.assertTreeTag(dec[3], name='Animal/Mammal/Cat', depth=3)
        self.assertTreeTag(dec[4], name='Animal/Mammal/Dog', depth=3)
        
    def test_descendants_l2(self):
        "Check l3 descendants found from l2"
        # Look down from Animal
        t1 = self.tag_model.objects.get(name='Animal/Mammal')
        self.assertTreeTag(t1, name='Animal/Mammal', depth=2)
        dec = t1.get_descendants()
        self.assertEqual(len(dec), 2)
        self.assertTreeTag(dec[0], name='Animal/Mammal/Cat', depth=3)
        self.assertTreeTag(dec[1], name='Animal/Mammal/Dog', depth=3)

    def test_descendants_l2(self):
        "Check no descendants found from l3"
        # Look down from Animal
        t1 = self.tag_model.objects.get(name='Animal/Insect/Bee')
        self.assertTreeTag(t1, name='Animal/Insect/Bee', depth=3)
        dec = t1.get_descendants()
        self.assertEqual(len(dec), 0)


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
            t1, name='One', label='One', slug='one', path='one', depth=1,
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, depth=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, count=1, depth=3,
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
            t1, name='One', label='One', slug='one', path='one', depth=1
        )
        self.assertTreeTag(
            t2, name='One/Two', label='Two', slug='two', path='one/two',
            parent=t1, depth=2,
        )
        self.assertTreeTag(
            t3, name='One/Two/Three', label='Three',
            slug='three', path='one/two/three',
            parent=t2, depth=3, count=1,
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
