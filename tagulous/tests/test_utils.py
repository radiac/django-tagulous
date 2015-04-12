"""
Tagulous test: Utils

Modules tested:
    tagulous.utils
"""
from tagulous.tests.lib import *


class UtilsTest(TestCase):
    """
    Test TagOptions
    """
    def test_parse_tags_commas(self):
        tags = tag_utils.parse_tags("adam,brian,chris")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
    
    def test_parse_tags_spaces(self):
        tags = tag_utils.parse_tags("adam brian chris")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        
    def test_parse_tags_commas_and_spaces(self):
        tags = tag_utils.parse_tags("adam, brian chris")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian chris")
        
    def test_parse_tags_commas_over_spaces(self):
        tags = tag_utils.parse_tags("adam brian  ,  chris")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam brian")
        self.assertEqual(tags[1], "chris")
        
    def test_parse_tags_order(self):
        tags = tag_utils.parse_tags("chris, adam, brian")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        
    def test_parse_tags_quotes(self):
        tags = tag_utils.parse_tags('"adam, one"')
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "adam, one")
        
    def test_parse_tags_quotes_comma_delim(self):
        tags = tag_utils.parse_tags('"adam, one","brian, two","chris, three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam, one")
        self.assertEqual(tags[1], "brian, two")
        self.assertEqual(tags[2], "chris, three")
        
    def test_parse_tags_quotes_space_delim(self):
        tags = tag_utils.parse_tags('"adam one" "brian two" "chris three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam one")
        self.assertEqual(tags[1], "brian two")
        self.assertEqual(tags[2], "chris three")
        
    def test_parse_tags_quotes_comma_delim_spaces_ignored(self):
        tags = tag_utils.parse_tags('"adam, one"  ,  "brian, two"  ,  "chris, three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam, one")
        self.assertEqual(tags[1], "brian, two")
        self.assertEqual(tags[2], "chris, three")
        
    def test_parse_tags_quotes_comma_delim_early_wins(self):
        tags = tag_utils.parse_tags('"adam one","brian two" "chris three"')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam one")
        self.assertEqual(tags[1], 'brian two" "chris three')
        
    def test_parse_tags_quotes_comma_delim_late_wins(self):
        tags = tag_utils.parse_tags('"adam one" "brian two","chris three"')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam one" "brian two')
        self.assertEqual(tags[1], "chris three")
        
    def test_parse_tags_quotes_dont_delimit(self):
        tags = tag_utils.parse_tags('adam"brian,chris dave')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam"brian')
        self.assertEqual(tags[1], "chris dave")
        
    def test_parse_tags_quotes_dont_close(self):
        tags = tag_utils.parse_tags('"adam,one","brian,two","chris, dave')
        self.assertEqual(len(tags), 3)
        # Will be sorted, " comes first
        self.assertEqual(tags[0], '"chris, dave')
        self.assertEqual(tags[1], "adam,one")
        self.assertEqual(tags[2], "brian,two")
    
    def test_parse_tags_quotes_and_unquoted(self):
        tags = tag_utils.parse_tags('adam , "brian, chris" , dave')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian, chris")
        self.assertEqual(tags[2], "dave")
    
    def test_parse_tags_quotes_order(self):
        tags = tag_utils.parse_tags('chris, "adam", brian')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        
    def test_parse_tags_quotes_escaped(self):
        """
        Tests quotes when delimiter is already comma
        """
        tags = tag_utils.parse_tags('adam, br""ian, ""chris, dave""')
        self.assertEqual(len(tags), 4)
        self.assertEqual(tags[0], '"chris')
        self.assertEqual(tags[1], 'adam')
        self.assertEqual(tags[2], 'br"ian')
        self.assertEqual(tags[3], 'dave"')
        
    def test_parse_tags_quotes_escaped_late(self):
        """
        Tests quotes when delimiter switches to comma
        """
        tags = tag_utils.parse_tags('""adam"" brian"", chris')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], '"adam" brian"')
        self.assertEqual(tags[1], 'chris')
        
    def test_parse_tags_empty_tag(self):
        tags = tag_utils.parse_tags('"adam" , , brian , ')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        
    def test_parse_tags_limit(self):
        with self.assertRaises(ValueError) as cm:
            print tag_utils.parse_tags("adam,brian,chris", 1)
        e = cm.exception
        self.assertEqual(str(e), 'This field can only have 1 argument')

    def test_parse_tags_limit_quotes(self):
        with self.assertRaises(ValueError) as cm:
            print tag_utils.parse_tags('"adam","brian",chris', 2)
        e = cm.exception
        self.assertEqual(str(e), 'This field can only have 2 arguments')

    def test_render_tags(self):
        tagstr = tag_utils.render_tags(['adam', 'brian', 'chris']);
        self.assertEqual(tagstr, 'adam, brian, chris')
    
    def test_render_tags_escapes_quotes(self):
        tagstr = tag_utils.render_tags(['ad"am', '"brian', 'chris"', '"dave"'])
        self.assertEqual(tagstr, '""brian, ""dave"", ad""am, chris""')
    
    def test_render_tags_quotes_commas_and_spaces(self):
        tagstr = tag_utils.render_tags(['adam brian', 'chris, dave', 'ed'])
        self.assertEqual(tagstr, '"adam brian", "chris, dave", ed')
    
    def test_parse_renders_tags(self):
        tagstr = 'adam, brian, chris'
        tags = tag_utils.parse_tags(tagstr)
        tagstr2 = tag_utils.render_tags(tags)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], 'adam')
        self.assertEqual(tags[1], 'brian')
        self.assertEqual(tags[2], 'chris')
        self.assertEqual(tagstr, tagstr2)
    
    def test_parse_renders_tags_complex(self):
        tagstr = '"""adam brian"", ""chris, dave", "ed, frank", gary'
        tags = tag_utils.parse_tags(tagstr)
        tagstr2 = tag_utils.render_tags(tags)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], '"adam brian", "chris, dave')
        self.assertEqual(tags[1], 'ed, frank')
        self.assertEqual(tags[2], 'gary')
        self.assertEqual(tagstr, tagstr2)
        