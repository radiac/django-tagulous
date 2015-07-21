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
    
    def test_override_defaults(self):
        opt = tag_models.TagOptions(
            force_lowercase=True,
            case_sensitive=True,
        )
        local_args = {
            'force_lowercase':  True,
            'case_sensitive':   True,
        }
        self.assertEqual(opt.items(with_defaults=False), local_args)
        expected = {}
        expected.update(tag_constants.OPTION_DEFAULTS)
        expected.update(local_args)
        self.assertEqual(opt.items(), expected)
        self.assertEqual(opt.field_items(with_defaults=False), local_args)
        self.assertEqual(opt.field_items(), dict([
            (k, v) for k, v in expected.items()
            if k in tag_constants.FIELD_OPTIONS
        ]))
    
    def test_initial_none(self):
        opt = tag_models.TagOptions(initial=None)
        self.assertEqual(opt.initial_string, '')
        self.assertEqual(opt.initial, [])
    
    def test_initial_string(self):
        opt = tag_models.TagOptions(initial='one, two')
        self.assertEqual(opt.initial_string, 'one, two')
        self.assertEqual(opt.initial, ['one', 'two'])
    
    def test_initial_list(self):
        opt = tag_models.TagOptions(initial=['one', 'two'])
        self.assertEqual(opt.initial_string, 'one, two')
        self.assertEqual(opt.initial, ['one', 'two'])
        self.assertEqual(opt.force_lowercase, False)
    
    def test_set_invalid(self):
        with self.assertRaises(AttributeError) as cm:
            tag_models.TagOptions(invalid=False)
        self.assertEqual(str(cm.exception), "invalid")

    def test_get_invalid(self):
        opt = tag_models.TagOptions()
        with self.assertRaises(AttributeError) as cm:
            opt.invalid
        self.assertEqual(str(cm.exception), "invalid")
