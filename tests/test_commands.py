"""
Tagulous test: manage.py commands

Modules tested:
    tagulous.management.commands.initial_tags
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management import call_command
from django.utils import six

from tests.lib import *


# If True, display output from call_command - use for debugging tests
DISPLAY_CALL_COMMAND = False


###############################################################################
####### ./manage.py initial_tags
###############################################################################

class InitialTagsTest(TagTestManager, TestCase):
    """
    Test initial_tags command
    """
    # Don't list the models in manage_models, otherwise TagTestManager will
    # initialise the tags for us
    def setUpExtra(self):
        self.singletag_model = test_models.SingleTagFieldOptionsModel.initial_list
        self.singletag_model_alt = test_models.SingleTagFieldOptionsModel.initial_string
        self.tag_model = test_models.TagFieldOptionsModel.initial_list
        self.singletag_model_2 = test_models2.MixedModel.singletag
        self.tag_model_2 = test_models2.MixedModel.tags
        
    def assertModelsEmpty(self):
        self.assertTagModel(self.singletag_model, {})
        self.assertTagModel(self.singletag_model_alt, {})
        self.assertTagModel(self.tag_model, {})
        self.assertTagModel(self.singletag_model_2, {})
        self.assertTagModel(self.tag_model_2, {})
    
    def assertSingleTagFilled(self, model):
        self.assertTagModel(model, {
            'Mr':   0,
            'Mrs':  0,
            'Ms':   0,
        })
    def assertTagFilled(self, model):
        self.assertTagModel(model, {
            'Adam': 0,
            'Brian': 0,
            'Chris': 0,
        })
    
    def run_command(self, target=''):
        with Capturing() as output:
            call_command(
                'initial_tags',
                target=target,  # Optional target
                verbosity=1,    # Silent
            )
            
        if DISPLAY_CALL_COMMAND:
            print(">> initial_tags target=%s" % target)
            print('\n'.join(output))
            print("<<<<<<<<<<")
        
        return output
        
    def test_load_all(self):
        "Check no target loads all"
        self.assertModelsEmpty()
        output = self.run_command()
        
        # Output correct if at least expected fields are loaded (more in apps)
        expected = [
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_list',
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_string',
            'tagulous_tests_app.TagFieldOptionsModel.initial_list',
            'tagulous_tests_app2.MixedModel.singletag',
            'tagulous_tests_app2.MixedModel.tags',
        ]
        self.assertGreaterEqual(len(output), len(expected))
        for field in expected:
            self.assertTrue('Loading initial tags for %s' % field in output)
        
        # All loaded
        self.assertSingleTagFilled(self.singletag_model)
        self.assertSingleTagFilled(self.singletag_model_alt)
        self.assertTagFilled(self.tag_model)
        self.assertSingleTagFilled(self.singletag_model_2)
        self.assertTagFilled(self.tag_model_2)
    
    def test_load_app(self):
        "Check app target just loads that app"
        self.assertModelsEmpty()
        output = self.run_command('tagulous_tests_app')
        
        # Output correct if at least expected fields are loaded (more in apps)
        expected = [
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_list',
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_string',
            'tagulous_tests_app.TagFieldOptionsModel.initial_list',
        ]
        self.assertGreaterEqual(len(output), len(expected))
        for field in expected:
            self.assertTrue('Loading initial tags for %s' % field in output)
        
        # Test app 1 loaded
        self.assertSingleTagFilled(self.singletag_model)
        self.assertSingleTagFilled(self.singletag_model_alt)
        self.assertTagFilled(self.tag_model)
        
        # Test app 2 empty
        self.assertTagModel(self.singletag_model_2, {})
        self.assertTagModel(self.tag_model_2, {})
    
    def test_load_model(self):
        "Check app and model target just loads that model"
        self.assertModelsEmpty()
        output = self.run_command(
            'tagulous_tests_app.SingleTagFieldOptionsModel'
        )
        
        # Output correct if at least expected fields are loaded (more in model)
        expected = [
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_list',
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_string',
        ]
        self.assertGreaterEqual(len(output), len(expected))
        for field in expected:
            self.assertTrue('Loading initial tags for %s' % field in output)
        
        # SingleTagFieldOptionsModel loaded
        self.assertSingleTagFilled(self.singletag_model)
        self.assertSingleTagFilled(self.singletag_model_alt)
        
        # Rest not loaded
        self.assertTagModel(self.tag_model, {})
        self.assertTagModel(self.singletag_model_2, {})
        self.assertTagModel(self.tag_model_2, {})
    
    def test_load_field(self):
        "Check app, model and field target just loads that field"
        self.assertModelsEmpty()
        output = self.run_command(
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_list'
        )
        
        # Output correct if only expected fields are loaded
        expected = [
            'tagulous_tests_app.SingleTagFieldOptionsModel.initial_list',
        ]
        self.assertEqual(len(output), len(expected))
        for field in expected:
            self.assertTrue('Loading initial tags for %s' % field in output)
        
        # SingleTagFieldOptionsModel loaded
        self.assertSingleTagFilled(self.singletag_model)
        
        # Rest not loaded
        self.assertTagModel(self.singletag_model_alt, {})
        self.assertTagModel(self.tag_model, {})
        self.assertTagModel(self.singletag_model_2, {})
        self.assertTagModel(self.tag_model_2, {})

    def test_load_field_empty(self):
        "Check loading a field which is empty prints the message"
        self.assertModelsEmpty()
        field = 'tagulous_tests_app.SingleTagFieldOptionsModel.protect_all_true'
        output = self.run_command(field)
        self.assertSequenceEqual(output, [
            'Nothing to load for %s' % field,
        ])
        self.assertModelsEmpty()
