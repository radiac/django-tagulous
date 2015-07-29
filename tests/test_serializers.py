"""
Tagulous test of serializers, dumpdata and loaddata

Modules tested:
    tagulous.serializers.*
"""
from __future__ import absolute_import
import json
import os
import tempfile
import six

from django.core import management

from tests.lib import *


# Copy of django's tests/fixtures/tests.py -> DumpDataAssertMixin
class DumpDataAssertMixin(object):

    def _dumpdata_assert(self, args, output, format='json', filename=None,
                         natural_foreign_keys=False, natural_primary_keys=False,
                         use_base_manager=False, exclude_list=[], primary_keys=''):
        new_io = six.StringIO()
        if filename:
            filename = os.path.join(tempfile.gettempdir(), filename)
        management.call_command('dumpdata', *args, **{'format': format,
                                                      'stdout': new_io,
                                                      'stderr': new_io,
                                                      'output': filename,
                                                      'use_natural_foreign_keys': natural_foreign_keys,
                                                      'use_natural_primary_keys': natural_primary_keys,
                                                      'use_base_manager': use_base_manager,
                                                      'exclude': exclude_list,
                                                      'primary_keys': primary_keys})
        if filename:
            with open(filename, "r") as f:
                command_output = f.read()
            os.remove(filename)
        else:
            command_output = new_io.getvalue().strip()
        
        if format == "json":
            self.assertJSONEqual(command_output, output)
        elif format == "xml":
            self.assertXMLEqual(command_output, output)
        else:
            self.assertEqual(command_output, output)


fixture_root = os.path.join(
    os.path.dirname(__file__), 'tagulous_tests_app', 'fixtures'
)


###############################################################################
####### Base class for common test functionality
###############################################################################

class SerializationTestMixin(DumpDataAssertMixin):
    """
    Test JSON serializer
    """
    manage_models = [
        test_models.SimpleMixedTest,
    ]
    fixture_format = 'undefined'
    
    def setUpExtra(self):
        self.model = test_models.SimpleMixedTest
        self.singletag_model = self.model.singletag.tag_model
        self.tags_model = self.model.tags.tag_model
        self.fixture_name = 'test_fixtures.%s' % self.fixture_format
        self.fixture_path = os.path.join(fixture_root, self.fixture_name)
    
    def _parse_for_cmp(self, raw):
        "Parse raw ready for _dumpdata_assert"
        return raw
        
    def test_dumpdata(self):
        # Populate
        self.model.objects.create(name='Test 1', singletag='single1', tags='tag1, tag2')
        self.model.objects.create(name='Test 2', singletag='single2', tags='tag3, tag4')
        
        # Get fixture
        with open(self.fixture_path, 'r') as f:
            fixture_data = self._parse_for_cmp(f.read())
        
        self._dumpdata_assert([
            'tagulous_tests_app._Tagulous_SimpleMixedTest_singletag',
            'tagulous_tests_app._Tagulous_SimpleMixedTest_tags',
            'tagulous_tests_app.SimpleMixedTest',
        ], fixture_data, format=self.fixture_format)
    
    def test_loaddata(self):
        self.assertEqual(self.model.objects.count(), 0)
        self.assertTagModel(self.singletag_model, {})
        self.assertTagModel(self.tags_model, {})
        
        management.call_command('loaddata', self.fixture_name, verbosity=0)
        t1 = self.model.objects.get(name='Test 1')
        t2 = self.model.objects.get(name='Test 2')
        
        self.assertInstanceEqual(
            t1, name='Test 1', singletag='single1', tags='tag1, tag2',
        )
        self.assertInstanceEqual(
            t2, name='Test 2', singletag='single2', tags='tag3, tag4',
        )
        self.assertEqual(t1.singletag.name, 'single1')
        self.assertEqual(t2.singletag.name, 'single2')
        self.assertEqual(t1.tags.count(), 2)
        self.assertEqual(t2.tags.count(), 2)
        self.assertTagModel(self.singletag_model, {
            'single1': 1,
            'single2': 1,
        })
        self.assertTagModel(self.tags_model, {
            'tag1': 1,
            'tag2': 1,
            'tag3': 1,
            'tag4': 1,
        })


###############################################################################
####### JSON
###############################################################################

class JsonSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test JSON serializer
    """
    fixture_format = 'json'
        
    def _parse_for_cmp(self, raw):
        "Parse raw ready for _dumpdata_assert"
        return json.loads(raw)


###############################################################################
####### YAML
###############################################################################

try:
    import yaml
except ImportError:
    yaml = None

@unittest.skipIf(yaml is None, 'pyyaml is not installed')
class YamlSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test YAML serializer
    """
    fixture_format = 'yaml'


###############################################################################
####### XML
###############################################################################

class XmlSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test XML serializer
    """
    fixture_format = 'xml'
