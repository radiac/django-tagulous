import unittest

from django.db import models
from django.core import exceptions
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User

from tagulous import constants as tag_constants
from tagulous import models as tag_models
from tagulous import forms as tag_forms
from tagulous import utils as tag_utils
from tagulous import settings as tag_settings

from tagulous.tests.app import models as test_models
from tagulous.tests.app import forms as test_forms


class TagTestManager(object):
    """
    Test mixin to help test tag models
    """
    manage_models = None
    
    def setUp(self):
        """
        Ensure initial data is in the tag models
        """
        if self.manage_models is not None:
            for model in self.manage_models:
                tag_models.initial.model_initialise_tags(model)
                tag_models.initial.model_initialise_tags(model)
        
        if hasattr(self, 'setUpExtra'):
            self.setUpExtra()
        
    def create(self, model, **kwargs):
        ##30# ++ This can be replaced when we've got create() working properly
        normal = {}
        tagfield = {}
        mmfield = {}
        for field_name, val in kwargs.items():
            if isinstance(
                model._meta.get_field(field_name), tag_models.TagField
            ):
                tagfield[field_name] = val
            elif isinstance(
                model._meta.get_field(field_name), models.ManyToManyField
            ):
                mmfield[field_name] = val
            else:
                normal[field_name] = val
        
        # Create as normal
        item = model.objects.create(**normal)
        
        # Add tagfields (may not be using enhanced queryset)
        for field_name, val in tagfield.items():
            setattr(item, field_name, val)
            getattr(item, field_name).save()
        
        # Add mm fields
        for field_name, val in mmfield.items():
            field = getattr(item, field_name)
            for obj in val:
                field.add(obj)
        
        return item
    
    def assertInstanceEqual(self, instance, **kwargs):
        # First, reload instance
        instance = instance.__class__.objects.get(pk=instance.pk)
        
        # Check values
        for field_name, val in kwargs.items():
            try:
                if isinstance(
                    instance.__class__._meta.get_field(field_name),
                    (tag_models.SingleTagField, tag_models.TagField)
                ) and isinstance(val, basestring):
                    self.assertEqual(str(getattr(instance, field_name)), val)
                elif isinstance(
                    instance.__class__._meta.get_field(field_name),
                    models.ManyToManyField
                ):
                    mm_objs = list(getattr(instance, field_name).all())
                    self.assertEqual(len(val), len(mm_objs))
                    for obj in val:
                        self.assertTrue(obj in mm_objs)
                else:
                    self.assertEqual(getattr(instance, field_name), val)
            except AssertionError, e:
                self.fail(
                    'Instances not equal for field %s: %s' % (field_name, e)
                )

    def assertTagModel(self, model, tag_counts):
        """
        Assert the tag model matches the specified tag counts
        """
        if isinstance(model, (tag_models.SingleTagDescriptor, tag_models.TagDescriptor)):
            model = model.tag_model
        
        if len(tag_counts) != model.objects.count():
            self.fail("Incorrect number of tags in '%s'; expected %d, got %d" % (model, len(tag_counts), model.objects.count()))
        
        for tag_name, count in tag_counts.items():
            try:
                tag = model.objects.get(name=tag_name)
            except model.DoesNotExist:
                self.fail("Tag model missing expected tag '%s'" % tag_name)
            if tag.count != count:
                self.fail("Tag count for '%s' incorrect; expected %d, got %d" % (tag_name, count, tag.count))
        
    def debugTagModel(self, model):
        """
        Print tag model tags and their counts, to help debugging failed tests
        """
        print "-=-=-=-=-=-"
        if isinstance(model, (tag_models.SingleTagDescriptor, tag_models.TagDescriptor)):
            model = model.tag_model
        print "Tag model: %s" % model
        for tag in model.objects.all():
            print '%s: %d' % (tag.name, tag.count)
        print "-=-=-=-=-=-"

