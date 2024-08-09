"""
Tagulous test of serializers, dumpdata and loaddata

Modules tested:
    tagulous.serializers.*
"""

# There were originally separate tests for loaddata and dumpdata, but these were
# combined because in Django <1.8 serializer order was not deterministic.
#
# This has been addressed, so we can look at splitting them again when these tests need
# refactoring
#
import os
import re
import tempfile
import unittest
from io import StringIO

from django.core import management, serializers
from django.test import TestCase

from tests.lib import TagTestManager, testenv
from tests.tagulous_tests_app import models as test_models

try:
    import yaml
except ImportError:
    yaml = None


RE_STRIP_PK_JSON = re.compile(r'("(pk|fk)": \d+|"mm": \[[0-9, ]*\])')
RE_STRIP_PK_YAML = re.compile(r"((pk|fk): \d+|mm:\s*(\n\s*- \d+)+)")
RE_STRIP_PK_XML = re.compile(r'(pk="\d+"|<field name="fk"[^>]+>\d+</field>)')


class DumpDataAssertMixin(object):
    # Based on django's tests/fixtures/tests.py -> DumpDataAssertMixin
    # but without comparisons due to django#24558
    def _dumpdata(
        self,
        args,
        format="json",
        filename=None,
        natural_foreign_keys=False,
        natural_primary_keys=False,
        use_base_manager=False,
        exclude_list=[],
        primary_keys="",
    ):
        new_io = StringIO()
        if filename:
            filename = os.path.join(tempfile.gettempdir(), filename)
        management.call_command(
            "dumpdata",
            *args,
            **{
                "format": format,
                "stdout": new_io,
                "stderr": new_io,
                "output": filename,
                "use_natural_foreign_keys": natural_foreign_keys,
                "use_natural_primary_keys": natural_primary_keys,
                "use_base_manager": use_base_manager,
                "exclude": exclude_list,
                "primary_keys": primary_keys,
            },
        )
        if filename:
            with open(filename, "r") as f:
                command_output = f.read()
            os.remove(filename)
        else:
            command_output = new_io.getvalue().strip()

        # Return early, do comparison outside this mixin
        return command_output


fixture_root = os.path.join(os.path.dirname(__file__), "tagulous_tests_app", "fixtures")


# ##############################################################################
# ###### Test serialization of a tagged model
# ##############################################################################


class SerializationTestMixin(DumpDataAssertMixin):
    """
    Test JSON serializer
    """

    manage_models = [test_models.SimpleMixedTest]
    dump_models = [
        "tagulous_tests_app.Tagulous_SimpleMixedTest_singletag",
        "tagulous_tests_app.Tagulous_SimpleMixedTest_tags",
        "tagulous_tests_app.SimpleMixedTest",
    ]
    fixture_format = "undefined"
    fixture_prefix = "simple"

    def setUpExtra(self):
        self.model = test_models.SimpleMixedTest
        self.singletag_model = self.model.singletag.tag_model
        self.tags_model = self.model.tags.tag_model
        self.fixture_name = "test_fixtures.%s" % self.fixture_format
        self.fixture_path = os.path.join(
            fixture_root, "{}_{}".format(self.fixture_prefix, self.fixture_name)
        )

        # Need to dump to loadable file due to django#24558
        self.tmp_fixture_name = "tmp_%s_%s" % (testenv, self.fixture_name)
        self.tmp_fixture_path = os.path.join(fixture_root, self.tmp_fixture_name)

        # Delete file if it exists
        if os.path.exists(self.tmp_fixture_path):
            os.remove(self.tmp_fixture_path)

    def tearDownExtra(self):
        if os.path.exists(self.tmp_fixture_path):
            os.remove(self.tmp_fixture_path)

    def _populate(self):
        self.t1 = self.model.objects.create(
            name="Test 1", singletag="single1", tags="tag1, tag2"
        )
        self.t2 = self.model.objects.create(
            name="Test 2", singletag="single2", tags="tag3, tag4"
        )

    def _check(self):
        t1 = self.model.objects.get(name="Test 1")
        t2 = self.model.objects.get(name="Test 2")
        self.assertInstanceEqual(
            t1, name="Test 1", singletag="single1", tags="tag1, tag2"
        )
        self.assertInstanceEqual(
            t2, name="Test 2", singletag="single2", tags="tag3, tag4"
        )
        self.assertEqual(t1.singletag.name, "single1")
        self.assertEqual(t2.singletag.name, "single2")
        self.assertEqual(t1.tags.count(), 2)
        self.assertEqual(t2.tags.count(), 2)
        self.assertTagModel(self.singletag_model, {"single1": 1, "single2": 1})
        self.assertTagModel(
            self.tags_model, {"tag1": 1, "tag2": 1, "tag3": 1, "tag4": 1}
        )

    def _assert_dumped(self, dumped):
        with open(self.fixture_path) as file:
            raw = file.read()
        self.assert_equivalent(raw, dumped)

    def assert_equivalent(self, left, right):
        """
        Assert two fixtures are equivalent, allowing for pk variation
        """
        left = self.re_strip_pk.sub("", left)
        right = self.re_strip_pk.sub("", right)
        self.assertEqual(left, right)

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
        with open(self.tmp_fixture_path, "w") as f:
            f.write(dumped)

        # Empty the database
        self._empty()

        # Now load fixture
        management.call_command("loaddata", self.tmp_fixture_name, verbosity=0)

        # Check they were loaded correctly
        self._check()


class JsonSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    "Test JSON serializer"

    fixture_format = "json"
    re_strip_pk = RE_STRIP_PK_JSON


@unittest.skipIf(yaml is None, "pyyaml is not installed")
class YamlSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test YAML serializer
    """

    fixture_format = "yaml"
    re_strip_pk = RE_STRIP_PK_YAML


class XmlSerializationTest(SerializationTestMixin, TagTestManager, TestCase):
    """
    Test XML serializer
    """

    fixture_format = "xml"
    re_strip_pk = RE_STRIP_PK_XML


# ##############################################################################
# ###### Check serialization of tagged model with conventional FK and M2M fields
# ##############################################################################


class MixedTestMixin(SerializationTestMixin):
    manage_models = [test_models.MixedNonTagRefTest]
    dump_models = [
        "tagulous_tests_app.MixedNonTagModel",
        "tagulous_tests_app.MixedNonTagRefTest",
    ]
    fixture_prefix = "mixed"

    def setUpExtra(self):
        self.model = test_models.MixedNonTagRefTest
        self.tag_model = test_models.MixedNonTagModel
        self.fixture_name = "test_fixtures.%s" % self.fixture_format
        self.fixture_path = os.path.join(
            fixture_root, "{}_{}".format(self.fixture_prefix, self.fixture_name)
        )

        # Need to dump to loadable file due to django#24558
        self.tmp_fixture_name = "tmp_%s_%s" % (testenv, self.fixture_name)
        self.tmp_fixture_path = os.path.join(fixture_root, self.tmp_fixture_name)

        # Delete file if it exists
        if os.path.exists(self.tmp_fixture_path):
            os.remove(self.tmp_fixture_path)

    def _populate(self):
        tag1 = self.tag_model.objects.create(name="tag1")
        tag2 = self.tag_model.objects.create(name="tag2")
        tag3 = self.tag_model.objects.create(name="tag3")
        tag4 = self.tag_model.objects.create(name="tag4")
        self.t1 = self.model.objects.create(
            name="Test 1", singletag=tag1, tags=[tag1, tag2], fk=tag1
        )
        self.t1.mm.add(tag1, tag2)
        self.t2 = self.model.objects.create(
            name="Test 2", singletag=tag2, tags=[tag3, tag4], fk=tag2
        )
        self.t2.mm.add(tag3, tag4)

    def _check(self):
        t1 = self.model.objects.get(name="Test 1")
        t2 = self.model.objects.get(name="Test 2")
        tag1 = self.tag_model.objects.get(name="tag1")
        tag2 = self.tag_model.objects.get(name="tag2")
        tag3 = self.tag_model.objects.get(name="tag3")
        tag4 = self.tag_model.objects.get(name="tag4")
        self.assertInstanceEqual(
            t1,
            name="Test 1",
            singletag="tag1",
            tags="tag1, tag2",
            fk="tag1",
            mm=[tag1, tag2],
        )
        self.assertInstanceEqual(
            t2,
            name="Test 2",
            singletag="tag2",
            tags="tag3, tag4",
            fk="tag2",
            mm=[tag3, tag4],
        )
        self.assertTagModel(
            self.tag_model, {"tag1": 2, "tag2": 2, "tag3": 1, "tag4": 1}
        )

    def _empty(self):
        self.t1.delete()
        self.t2.delete()
        self.tag_model.objects.all().delete()
        self.assertEqual(self.model.objects.count(), 0)
        self.assertTagModel(self.tag_model, {})


class MixedJsonSerializationTest(MixedTestMixin, TagTestManager, TestCase):
    "Test JSON serializer with normal fk and m2m fields"

    fixture_format = "json"
    re_strip_pk = RE_STRIP_PK_JSON


@unittest.skipIf(yaml is None, "pyyaml is not installed")
class MixedYamlSerializationTest(MixedTestMixin, TagTestManager, TestCase):
    "Test Yaml serializer with normal fk and m2m fields"

    fixture_format = "yaml"
    re_strip_pk = RE_STRIP_PK_YAML


class MixedXmlSerializationTest(MixedTestMixin, TagTestManager, TestCase):
    "Test XML serializer with normal fk and m2m fields"

    fixture_format = "xml"
    re_strip_pk = RE_STRIP_PK_XML


# ##############################################################################
# ###### Other serialization tests
# ##############################################################################


class MixedTestMixin(TagTestManager, TestCase):
    def test_many_to_one(self):
        """
        Check serialization of a tagged model with reverse FKs
        """
        t1 = test_models.MixedRefTest.objects.create(
            name="test", singletag="test", tags="test"
        )
        rfk1 = test_models.ManyToOneTest.objects.create(name="rfk1", mixed_ref_test=t1)
        t1.refresh_from_db()
        self.assertEqual(t1.many_to_one.count(), 1)
        self.assertEqual(t1.many_to_one.first(), rfk1)

        serialized = serializers.serialize(
            "xml", test_models.MixedRefTest.objects.all()
        )
        deserialized = list(serializers.deserialize("xml", serialized))
        self.assertEqual(len(deserialized), 1)
        obj = deserialized[0].object
        self.assertInstanceEqual(obj, name="test", singletag="test", tags="test")
        self.assertEqual(obj.many_to_one.count(), 1)
        self.assertEqual(obj.many_to_one.first().name, "rfk1")
