"""
Tagulous test: Tag options

Modules tested:
    tagulous.options
    tagulous.constants
"""
from __future__ import absolute_import
from tests.lib import *


class TagOptionsTest(TestCase):
    """
    Test TagOptions
    """
    def test_defaults(self):
        opt = tag_models.TagOptions()
        self.assertEqual(opt.items(with_defaults=False), {})
        self.assertEqual(opt.items(), tag_constants.OPTION_DEFAULTS)
        self.assertEqual(opt.form_items(with_defaults=False), {})
        self.assertEqual(opt.form_items(), dict([
            (k, v) for k, v in tag_constants.OPTION_DEFAULTS.items()
            if k in tag_constants.FORM_OPTIONS
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
        self.assertEqual(opt.form_items(with_defaults=False), local_args)
        self.assertEqual(opt.form_items(), dict([
            (k, v) for k, v in expected.items()
            if k in tag_constants.FORM_OPTIONS
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

    def test_update_dict(self):
        opt = tag_models.TagOptions(initial='Adam, Brian')
        self.assertEqual(opt.initial_string, 'Adam, Brian')
        
        opt.update({'initial': 'Brian, Chris'})
        self.assertEqual(opt.initial_string, 'Brian, Chris')
        
    def test_update_object(self):
        opt1 = tag_models.TagOptions(initial='Adam, Brian')
        opt2 = tag_models.TagOptions(initial='Brian, Chris')
        self.assertEqual(opt1.initial_string, 'Adam, Brian')
        self.assertEqual(opt2.initial_string, 'Brian, Chris')
        
        opt1.update(opt2)
        self.assertEqual(opt1.initial_string, 'Brian, Chris')
    
    def test_set_missing_dict(self):
        opt = tag_models.TagOptions(initial='Adam, Brian')
        self.assertEqual(opt.initial_string, 'Adam, Brian')
        self.assertEqual(opt.force_lowercase, False)
        
        opt.set_missing({
            'initial':  'Brian, Chris',
            'force_lowercase': True,
        })
        self.assertEqual(opt.initial_string, 'Adam, Brian')
        self.assertEqual(opt.force_lowercase, True)
    
    def test_set_missing_object(self):
        opt1 = tag_models.TagOptions(initial='Adam, Brian')
        opt2 = tag_models.TagOptions(initial='Brian, Chris', force_lowercase=True)
        self.assertEqual(opt1.initial_string, 'Adam, Brian')
        self.assertEqual(opt1.force_lowercase, False)
        self.assertEqual(opt2.initial_string, 'Brian, Chris')
        self.assertEqual(opt2.force_lowercase, True)
        
        opt1.set_missing(opt2)
        self.assertEqual(opt1.initial_string, 'Adam, Brian')
        self.assertEqual(opt1.force_lowercase, True)
    
    def test_add(self):
        opt1 = tag_models.TagOptions(initial='Adam, Brian')
        opt2 = tag_models.TagOptions(force_lowercase=True)
        self.assertEqual(opt1.initial_string, 'Adam, Brian')
        self.assertEqual(opt1.force_lowercase, False)
        self.assertEqual(opt2.initial_string, '')
        self.assertEqual(opt2.force_lowercase, True)
        
        opt3 = opt1 + opt2
        self.assertEqual(opt3.initial_string, 'Adam, Brian')
        self.assertEqual(opt3.force_lowercase, True)
        self.assertNotEqual(id(opt1), id(opt2))
        self.assertNotEqual(id(opt2), id(opt3))
        self.assertNotEqual(id(opt3), id(opt1))
