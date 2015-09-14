"""
Tagulous test: View-related functionality

Modules tested:
    tagulous.views
"""
from __future__ import absolute_import
from tests.lib import *

from django.test import Client
from django.core.urlresolvers import reverse

# Django 1.4 is last to support Python 2.5, but json isn't available until 2.6
try:
    import json
except ImportError:
   from django.utils import simplejson as json

client = Client()


###############################################################################
####### Test tag forms with CBVs
###############################################################################

class TagFormCBVTest(TagTestManager, TestCase):
    "Test CBVs which use tagged forms"
    manage_models = [
        test_models.SimpleMixedTest,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.model = test_models.SimpleMixedTest
        self.singletag_model = self.model.singletag.tag_model
        self.tags_model = self.model.tags.tag_model
        
    def test_cbv_create(self):
        "Test CBV create"
        self.assertTagModel(self.singletag_model, {})
        self.assertTagModel(self.tags_model, {})
        
        # Create
        response = client.post(reverse('tagulous_tests_app-MixedCreate'), {
            'name': 'Test 1',
            'singletag': 'Mr',
            'tags': 'blue, red',
        })
        self.assertEqual(response.status_code, 302)
        
        # Get
        t1 = self.model.objects.get(name='Test 1')
        self.assertIsInstance(t1.singletag, tag_models.BaseTagModel)
        self.assertEqual(t1.singletag.name, 'Mr')
        self.assertEqual(t1.tags.count(), 2)
        self.assertEqual(t1.tags.all()[0], 'blue')
        self.assertEqual(t1.tags.all()[1], 'red')
        self.assertTagModel(self.singletag_model, {
            'Mr':   1,
        })
        self.assertTagModel(self.tags_model, {
            'blue': 1,
            'red':  1,
        })
    
    def test_cbv_update(self):
        "Test CBV update"
        # Set up object
        t1 = self.model.objects.create(
            name='Test 1',
            singletag='Mr',
            tags='blue, red',
        )
        self.assertTagModel(self.singletag_model, {
            'Mr':   1,
        })
        self.assertTagModel(self.tags_model, {
            'blue': 1,
            'red':  1,
        })
        
        # Update it
        response = client.post(
            reverse('tagulous_tests_app-MixedUpdate', kwargs={'pk': t1.pk}),
            {
                'name': 'Test 2',
                'singletag': 'Mrs',
                'tags': 'blue, green',
            }
        )
        self.assertEqual(response.status_code, 302)

        # Check
        t2 = self.model.objects.get(pk=t1.pk)
        self.assertIsInstance(t1.singletag, tag_models.BaseTagModel)
        self.assertEqual(t2.name, 'Test 2')
        self.assertEqual(t2.singletag.name, 'Mrs')
        self.assertEqual(t2.tags.count(), 2)
        self.assertEqual(t2.tags.all()[0], 'blue')
        self.assertEqual(t2.tags.all()[1], 'green')
        self.assertTagModel(self.singletag_model, {
            'Mrs':  1,
        })
        self.assertTagModel(self.tags_model, {
            'blue': 1,
            'green': 1,
        })


###############################################################################
####### Test autocomplete view
###############################################################################

class AutocompleteViewTest(TagTestManager, TestCase):
    "Test autocomplete view"
    manage_models = [
        test_models.TagFieldOptionsModel,
    ]
    
    def setUpExtra(self):
        # Load initial tags for all models which have them
        self.test_model = test_models.TagFieldOptionsModel
    
    def test_unlimited(self):
        "Test unlimited autocomplete view"
        # Add some tags
        tag_model = self.test_model.autocomplete_view.tag_model
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        response = client.get(
            reverse('tagulous_tests_app-unlimited'),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 100)
        for i in range(100):
            self.assertEqual(data['results'][i], 'tag%02d' % i)
        self.assertEqual(data['more'], False)
        
    def test_unlimited_query(self):
        "Test unlimited autocomplete view with query"
        # Add some tags
        tag_model = self.test_model.autocomplete_view.tag_model
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        response = client.get(
            reverse('tagulous_tests_app-unlimited'),
            {'q': 'tag0'},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 10)
        for i in range(10):
            self.assertEqual(data['results'][i], 'tag%02d' % i)
        self.assertEqual(data['more'], False)

    def test_limited(self):
        "Test limited autocomplete view"
        # Add some tags
        tag_model = self.test_model.autocomplete_limit.tag_model
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        page_length = tag_model.tag_options.autocomplete_limit
        self.assertEqual(page_length, 3)
        
        # Get page 1
        response = client.get(
            reverse('tagulous_tests_app-limited'),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), page_length)
        self.assertEqual(data['results'][0], 'tag00')
        self.assertEqual(data['results'][1], 'tag01')
        self.assertEqual(data['results'][2], 'tag02')
        self.assertEqual(data['more'], True)
        
        # Get page 4: starting 10th tag, tag09 to tag11
        page = 4
        response = client.get(
            reverse('tagulous_tests_app-limited'),
            {'p': page},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), page_length)
        self.assertEqual(data['results'][0], 'tag09')
        self.assertEqual(data['results'][1], 'tag10')
        self.assertEqual(data['results'][2], 'tag11')
        self.assertEqual(data['more'], True)
        
        # Get last page, 34: starting 100th tag, tag99
        page = 34
        response = client.get(
            reverse('tagulous_tests_app-limited'),
            {'p': page},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0], 'tag99')
        self.assertEqual(data['more'], False)
        
    def test_limited_query(self):
        "Test limited autocomplete view with query"
        # Add some tags
        tag_model = self.test_model.autocomplete_limit.tag_model
        for i in range(100):
            tag_model.objects.create(name="tag%02d" % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        page_length = tag_model.tag_options.autocomplete_limit
        self.assertEqual(page_length, 3)
        
        # Get page 1
        response = client.get(
            reverse('tagulous_tests_app-limited'),
            {'q': 'tag1'},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), page_length)
        self.assertEqual(data['results'][0], 'tag10')
        self.assertEqual(data['results'][1], 'tag11')
        self.assertEqual(data['results'][2], 'tag12')
        self.assertEqual(data['more'], True)
        
        # Get last page, 4: starting 10th tag, tag19
        page = 4
        response = client.get(
            reverse('tagulous_tests_app-limited'),
            {'q': 'tag1', 'p': page},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0], 'tag19')
        self.assertEqual(data['more'], False)
    
    def test_login(self):
        "Test autocomplete_login view"
        # Add some tags
        tag_model = self.test_model.autocomplete_view.tag_model
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        user = User.objects.create_user('test', 'test@example.com', 'password')
        client.login(username='test', password='password')
        response = client.get(
            reverse('tagulous_tests_app-login'),
        )
        client.logout()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 100)
        for i in range(100):
            self.assertEqual(data['results'][i], 'tag%02d' % i)
        self.assertEqual(data['more'], False)
        
    def test_queryset(self):
        "Test autocomplete view on a tag model queryset"
        # Add some tags
        tag_model = self.test_model.autocomplete_view.tag_model
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        response = client.get(
            reverse('tagulous_tests_app-queryset'),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 10)
        for i in range(10):
            self.assertEqual(data['results'][i], 'tag2%d' % i)
        self.assertEqual(data['more'], False)

    def test_force_lowercase_true(self):
        "Test autocomplete view on a tag model with force_lowercase=True"
        # Add some tags
        tag_model = self.test_model.force_lowercase_true.tag_model
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        response = client.get(
            reverse('tagulous_tests_app-force_lowercase_true'),
            {'q': 'Tag1'},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 10)
        for i in range(10):
            self.assertEqual(data['results'][i], 'tag1%d' % i)
        self.assertEqual(data['more'], False)

    def test_case_sensitive_false(self):
        "Test autocomplete view on a tag model with case_sensitive=False"
        # Add some tags
        tag_model = self.test_model.case_sensitive_false.tag_model
        tag_model.objects.all().delete() # clear out initial
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        response = client.get(
            reverse('tagulous_tests_app-case_sensitive_false'),
            {'q': 'Tag1'},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 10)
        for i in range(10):
            self.assertEqual(data['results'][i], 'tag1%d' % i)
        self.assertEqual(data['more'], False)

    def test_case_sensitive_true(self):
        "Test autocomplete view on a tag model with case_sensitive=True"
        # Add some tags
        tag_model = self.test_model.case_sensitive_true.tag_model
        tag_model.objects.all().delete() # clear out initial
        for i in range(100):
            tag_model.objects.create(name='tag%02d' % i)
        self.assertEqual(tag_model.objects.count(), 100)
        
        # Get them from view
        response = client.get(
            reverse('tagulous_tests_app-case_sensitive_true'),
            {'q': 'Tag1'},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        from django.db import connection
        if connection.vendor == 'sqlite':
            # Sqlite doesn't support case insensitive searches - expect to
            # get back 10 matches
            self.assertEqual(len(data['results']), 10)
            for i in range(10):
                self.assertEqual(data['results'][i], 'tag1%d' % i)
        else:
            self.assertEqual(len(data['results']), 0)
            self.assertEqual(data['more'], False)
