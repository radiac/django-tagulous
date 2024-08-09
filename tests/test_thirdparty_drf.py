"""
Test integration with third party library Django REST framework

https://www.django-rest-framework.org

To run these tests::

    pip install djangorestframework~=3.0
"""

import unittest

from django.conf import settings
from django.test import TestCase, override_settings

from tests.lib import TagTestManager
from tests.tagulous_tests_app.models import MixedTest

try:
    import rest_framework
    from rest_framework.serializers import ModelSerializer

    from tagulous.contrib.drf import TagSerializer

except ImportError:
    rest_framework = None

    class TagSerializer:
        pass

    ModelSerializer = TagSerializer


class MixedTestModelSerializer(ModelSerializer):
    class Meta:
        model = MixedTest
        fields = ["name", "singletag", "tags"]


class MixedTestTagSerializer(TagSerializer):
    class Meta:
        model = MixedTest
        fields = ["name", "singletag", "tags"]


@unittest.skipIf(rest_framework is None, "djangorestframework is not installed")
@override_settings(INSTALLED_APPS=settings.INSTALLED_APPS + ["rest_framework"])
class DRFTest(TagTestManager, TestCase):
    def test_model_serializer__serialises_to_pks(self):
        obj = MixedTest.objects.create(
            name="person", singletag="mr", tags="adam, brian, chris"
        )
        serializer = MixedTestModelSerializer(obj)
        self.assertSequenceEqual(
            serializer.data,
            {
                "name": "person",
                "singletag": obj.singletag.pk,
                "tags": [obj.pk for obj in obj.tags.all()],
            },
        )

    def test_model_serializer__create__deserialises_from_pks(self):
        # Prepare the tags
        mr = MixedTest.singletag.tag_model.objects.create(name="mr")
        adam = MixedTest.tags.tag_model.objects.create(name="adam")
        brian = MixedTest.tags.tag_model.objects.create(name="brian")
        chris = MixedTest.tags.tag_model.objects.create(name="chris")

        data = {
            "name": "person",
            "singletag": mr.pk,
            "tags": [adam.pk, brian.pk, chris.pk],
        }

        serializer = MixedTestModelSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(obj.name, "person")
        self.assertEqual(str(obj.singletag), "mr")
        self.assertEqual(str(obj.tags), "adam, brian, chris")

    def test_model_serializer__update__deserializes_from_pks(self):
        obj1 = MixedTest.objects.create(
            name="person", singletag="mrs", tags="alice, brenda, chloe"
        )

        mr = MixedTest.singletag.tag_model.objects.create(name="mr")
        adam = MixedTest.tags.tag_model.objects.create(name="adam")
        brian = MixedTest.tags.tag_model.objects.create(name="brian")
        chris = MixedTest.tags.tag_model.objects.create(name="chris")

        data = {
            "name": "person",
            "singletag": mr.pk,
            "tags": [adam.pk, brian.pk, chris.pk],
        }

        serializer = MixedTestModelSerializer(instance=obj1, data=data)
        self.assertTrue(serializer.is_valid())
        obj2 = serializer.save()
        self.assertEqual(obj2.name, "person")
        self.assertEqual(str(obj2.singletag), "mr")
        self.assertEqual(str(obj2.tags), "adam, brian, chris")

    def test_tag_serializer__serializes_to_strings(self):
        obj = MixedTest.objects.create(
            name="person", singletag="mr", tags="adam, brian, chris"
        )
        serializer = MixedTestTagSerializer(obj)
        self.assertSequenceEqual(
            serializer.data,
            {"name": "person", "singletag": "mr", "tags": ["adam", "brian", "chris"]},
        )

    def test_tag_serializer__create__deserializes_from_strings(self):
        data = {"name": "person", "singletag": "mr", "tags": ["adam", "brian", "chris"]}

        serializer = MixedTestTagSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(obj.name, "person")
        self.assertEqual(str(obj.singletag), "mr")
        self.assertEqual(str(obj.tags), "adam, brian, chris")

    def test_tag_serializer__update__deserializes_from_strings(self):
        obj1 = MixedTest.objects.create(
            name="person", singletag="mrs", tags="alice, brenda, chloe"
        )

        data = {"name": "person", "singletag": "mr", "tags": ["adam", "brian", "chris"]}

        serializer = MixedTestTagSerializer(instance=obj1, data=data)
        self.assertTrue(serializer.is_valid())
        obj2 = serializer.save()
        self.assertEqual(obj2.name, "person")
        self.assertEqual(str(obj2.singletag), "mr")
        self.assertEqual(str(obj2.tags), "adam, brian, chris")
