"""
Tagulous test of serializers, dumpdata and loaddata

Modules tested:
    tagulous.serializers.*
"""
# There were originally separate tests for loaddata and dumpdata, but have been
# combined because in Django 1.4-1.8 serializer order is not deterministic, ie
# order of keys in dicts can change, causing output order to change and
# comparisons to fail on values which are effectively the same. Testing
# dumpdata and loaddata in the same place isn't ideal, but the only other way
# is to implement non-deterministic comparisons for json, pyyaml and xml;
# patches welcome.
#
# This should be fixed in Django 1.9, at which point we can look at splitting
# them again - see https://code.djangoproject.com/ticket/24558

from __future__ import absolute_import
from __future__ import unicode_literals
import json
import os
import tempfile
import six

from django.core import management
from django.utils import six

from tests.lib import *

try:
    import yaml
except ImportError:
    yaml = None


# Based on django's tests/fixtures/tests.py -> DumpDataAssertMixin
# but without comparisons due to django#24558
class DumpDataAssertMixin(object):

    def _dumpdata(self, args, format='json', filename=None,
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
        
        # Return early, do comparison externally
        return command_output
        
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
####### Test serialization of a tagged model
###############################################################################

class SerializationTestMixin(DumpDataAssertMixin):
    """
    Test JSON serializer
    """
    manage_models = [
        test_models.SimpleMixedTest,
    ]
    dump_models = [
        'tagulous_tests_app._Tagulous_SimpleMixedTest_singletag',
        'tagulous_tests_app._Tagulous_SimpleMixedTest_tags',
        'tagulous_tests_app.SimpleMixedTest',
    ]
    fixture_format = 'undefined'
    
    def setUpExtra(self):
        self.model = test_models.SimpleMixedTest
        self.singletag_model = self.model.singletag.tag_model
        self.tags_model = self.model.tags.tag_model
        self.fixture_name = 'test_fixtures.%s' % self.fixture_format
        self.fixture_path = os.path.join(fixture_root, self.fixture_name)
        
        # Need to dump to loadable file due to django#24558
        self.tmp_fixture_name = 'tmp_%s_%s' % (testenv, self.fixture_name)
        self.tmp_fixture_path = os.path.join(fixture_root, self.tmp_fixture_name)
        
        # Delete file if it exists
        if os.path.exists(self.tmp_fixture_path):
            os.remove(self.tmp_fixture_path)
    
    def tearDownExtra(self):
        if os.path.exists(self.tmp_fixture_path):
            os.remove(self.tmp_fixture_path)
    
    def _populate(self):
        self.t1 = self.model.objects.create(name='Test 1', singletag='single1', tags='tag1, tag2')
        self.t2 = self.model.objects.create(name='Test 2', singletag='single2', tags='tag3, tag4')

    def _check(self):
        t1 = self.model.objects.get(name='Test 1')
        t2 = self.model.objects.get(name='Test 2')
        self.assertInstanceEqual(t1, name='Test 1', singletag='single1', tags='tag1, tag2')
        self.assertInstanceEqual(t2, name='Test 2', singletag='single2', tags='tag3, tag4')
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
    
    def _assert_dumped(self, dumped):
        # Basic checks to make sure it's not completely invalid
        # Cannot test in more detail without django#24558
        self.assertTrue('single1' in dumped)
        self.assertTrue('tag1' in dumped)

    def _empty(self):
        self.t1.delete()
        self.t2.delete()
        self.assertEqual(self.model.objects.count(), 0)
        self.assertTagModel(self.singletag_model, {})
        self.assertTagModel(self.tags_model, {})
    
    def test_dump_load(self):
        "Check dumpdata and loaddata recreate data"
        # Populate and confirm
        self._populate()
        self._check()
        
        # Dump
        dumped = self._dumpdata(self.dump_models, format=self.fixture_format)
        self._assert_dumped(dumped)
        
        # Fixture path
        with open(self.tmp_fixture_path, 'w') as f:
            f.write(dumped)
        
        # Empty the database
        self._empty()
        
        # Now load fixture
        management.call_command('loaddata', self.tmp_fixture_name, verbosity=0)
        
        # Check they were loaded correctly
        self._check()


class JsonSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    "Test JSON serializer"
    fixture_format = 'json'

@unittest.skipIf(yaml is None, 'pyyaml is not installed')
class YamlSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test YAML serializer
    """
    fixture_format = 'yaml'

class XmlSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test XML serializer
    """
    fixture_format = 'xml'


###############################################################################
####### Check serialization of tagged model with conventional FK and M2M fields
###############################################################################

class MixedTestMixin(SerializationTestMixin):
    manage_models = [
        test_models.MixedNonTagRefTest,
    ]
    dump_models = [
        'tagulous_tests_app.MixedNonTagModel',
        'tagulous_tests_app.MixedNonTagRefTest',
    ]
    
    def setUpExtra(self):
        self.model = test_models.MixedNonTagRefTest
        self.tag_model = test_models.MixedNonTagModel
        self.fixture_name = 'test_fixtures.%s' % self.fixture_format
        self.fixture_path = os.path.join(fixture_root, self.fixture_name)
        
        # Need to dump to loadable file due to django#24558
        self.tmp_fixture_name = 'tmp_%s_%s' % (testenv, self.fixture_name)
        self.tmp_fixture_path = os.path.join(fixture_root, self.tmp_fixture_name)
        
        # Delete file if it exists
        if os.path.exists(self.tmp_fixture_path):
            os.remove(self.tmp_fixture_path)
    
    def _populate(self):
        tag1 = self.tag_model.objects.create(name='tag1')
        tag2 = self.tag_model.objects.create(name='tag2')
        tag3 = self.tag_model.objects.create(name='tag3')
        tag4 = self.tag_model.objects.create(name='tag4')
        self.t1 = self.model.objects.create(
            name='Test 1', singletag=tag1, tags=[tag1, tag2], fk=tag1
        )
        self.t1.mm.add(tag1, tag2)
        self.t2 = self.model.objects.create(
            name='Test 2', singletag=tag2, tags=[tag3, tag4], fk=tag2
        )
        self.t2.mm.add(tag3, tag4)

    def _check(self):
        t1 = self.model.objects.get(name='Test 1')
        t2 = self.model.objects.get(name='Test 2')
        tag1 = self.tag_model.objects.get(name='tag1')
        tag2 = self.tag_model.objects.get(name='tag2')
        tag3 = self.tag_model.objects.get(name='tag3')
        tag4 = self.tag_model.objects.get(name='tag4')
        self.assertInstanceEqual(
            t1, name='Test 1', singletag='tag1', tags='tag1, tag2',
            fk='tag1', mm=[tag1, tag2]
        )
        self.assertInstanceEqual(
            t2, name='Test 2', singletag='tag2', tags='tag3, tag4',
            fk='tag2', mm=[tag3, tag4]
        )
        self.assertTagModel(self.tag_model, {
            'tag1': 2,
            'tag2': 2,
            'tag3': 1,
            'tag4': 1,
        })
    
    def _assert_dumped(self, dumped):
        # Basic checks to make sure it's not completely invalid
        # Cannot test in more detail without django#24558
        self.assertTrue('tag1' in dumped)
        self.assertTrue('tag2' in dumped)

    def _empty(self):
        self.t1.delete()
        self.t2.delete()
        self.tag_model.objects.all().delete()
        self.assertEqual(self.model.objects.count(), 0)
        self.assertTagModel(self.tag_model, {})

class MixedJsonSerializationTest(MixedTestMixin, TagTestManager, TestCase):
    "Test JSON serializer with normal fk and m2m fields"
    fixture_format = 'json'
    
@unittest.skipIf(yaml is None, 'pyyaml is not installed')
class MixedYamlSerializationTest(MixedTestMixin, TagTestManager, TestCase):
    "Test Yaml serializer with normal fk and m2m fields"
    fixture_format = 'yaml'
    
class MixedXmlSerializationTest(MixedTestMixin, TagTestManager, TestCase):
    "Test XML serializer with normal fk and m2m fields"
    fixture_format = 'xml'
