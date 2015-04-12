"""
Tagulous test: Tag options

Modules tested:
    tagulous.options
"""
from tagulous.tests.lib import *


class TagOptionsTest(TestCase):
    """
    Test TagOptions
    """
    def test_defaults(self):
        opt = tag_models.TagOptions()
        self.assertEqual(opt.items(with_defaults=False), {})
        self.assertEqual(opt.items(), tag_constants.OPTION_DEFAULTS)
        self.assertEqual(opt.field_items(with_defaults=False), {})
        self.assertEqual(opt.field_items(), dict([
            (k, v) for k, v in tag_constants.OPTION_DEFAULTS.items()
            if k in tag_constants.FIELD_OPTIONS
        ]))

    # ++ More tests:
    # ++ Set options in model field, access in form field
    # ++ Override options in formfield()
    # ++ Set options in form field
    # ++ Test each option and combo (in a single model with multiple fields)
    
