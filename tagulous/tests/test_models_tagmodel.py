"""
Tagulous test: Tag models

Modules tested:
    tagulous.models.models.BaseTagModel
    tagulous.models.models.TagModel
"""
from tagulous.tests.lib import *


class TagModelTest(TagTestManager, TestCase):
    """
    Test tag models
    """
    manage_models = [
        test_models.MixedTest,
        test_models.MixedRefTest,
    ]
    
    @unittest.skip("buggy")
    def test_merge_tags(self):
        tag_model = test_models.MixedTestTagModel
        
        # Set up database
        a1 = self.create(test_models.MixedTest, name='a1', singletags='one', tags='one')
        a2 = self.create(test_models.MixedTest, name='a2', singletags='two', tags='two')
        a3 = self.create(test_models.MixedTest, name='a3', singletags='three', tags='three')

        b1 = self.create(test_models.MixedRefTest, name='b1', singletags='one', tags='one')
        b2 = self.create(test_models.MixedRefTest, name='b2', singletags='two', tags='two')
        b3 = self.create(test_models.MixedRefTest, name='b3', singletags='three', tags='three')
        
        # Confirm it's correct
        self.assertTagModel(tag_model, {
            'one': 4,
            'two': 4,
            'three': 4,
        })
        self.assertInstanceEqual(a1, singletags='one', tags='one')
        self.assertInstanceEqual(a2, singletags='two', tags='two')
        self.assertInstanceEqual(a3, singletags='three', tags='three')
        self.assertInstanceEqual(b1, singletags='one', tags='one')
        self.assertInstanceEqual(b2, singletags='two', tags='two')
        self.assertInstanceEqual(b3, singletags='three', tags='three')
        
        # Merge tags
        self.assertEqual(tag_model.objects.count(), 3)
        s1 = tag_model.objects.get(name='one')
        s1.merge_tags(
            tag_model.objects.filter(name__in=['one', 'two', 'three'])
        )
        
        # Check it's correct
        #self.assertTagModel(tag_model, {
        #    'one': 12,
        #})
        self.assertInstanceEqual(a1, singletags='one', tags='one')
        self.assertInstanceEqual(a2, singletags='one', tags='one')
        self.assertInstanceEqual(a3, singletags='one', tags='one')
        self.assertInstanceEqual(b1, singletags='one', tags='one')
        self.assertInstanceEqual(b2, singletags='one', tags='one')
        self.assertInstanceEqual(b3, singletags='one', tags='one')

