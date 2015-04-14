"""
Tagulous test: Tag options

Modules tested:
    tagulous.options
    tagulous.constants
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

    # ++ More tests: overriding defaults, items(), field_items(), __add__
    
