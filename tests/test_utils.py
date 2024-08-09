# -*- coding: utf-8 -*-
"""
Tagulous test: Utils

Modules tested:
    tagulous.utils
"""

from django.test import TestCase

from tagulous import utils as tag_utils

# ##############################################################################
# ###### utils.strip_split()
# ##############################################################################


class UtilsSplitStripTest(TestCase):
    "Test utils.split_strip"

    def test_empty(self):
        split = tag_utils.split_strip(None)
        self.assertEqual(split, [])
        split = tag_utils.split_strip("")
        self.assertEqual(split, [])

    def test_spaceless(self):
        split = tag_utils.split_strip("adam,brian")
        self.assertEqual(len(split), 2)
        self.assertEqual(split[0], "adam")
        self.assertEqual(split[1], "brian")

    def test_spaced(self):
        split = tag_utils.split_strip("  adam  ,  brian  ")
        self.assertEqual(len(split), 2)
        self.assertEqual(split[0], "adam")
        self.assertEqual(split[1], "brian")


# ##############################################################################
# ###### utils.parse_tags
# ##############################################################################


class UtilsParseTagsTest(TestCase):
    "Test utils.parse_tags"

    def test_commas(self):
        tags = tag_utils.parse_tags("adam,brian,chris")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")

    def test_spaces(self):
        tags = tag_utils.parse_tags("adam brian chris")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")

    def test_trailing_comma(self):
        tags = tag_utils.parse_tags("adam,brian,")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")

    def test_trailing_space(self):
        tags = tag_utils.parse_tags("adam brian ")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")

    def test_commas_and_spaces(self):
        tags = tag_utils.parse_tags("adam, brian chris")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian chris")

    def test_commas_over_spaces(self):
        tags = tag_utils.parse_tags("adam brian  ,  chris")
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam brian")
        self.assertEqual(tags[1], "chris")

    def test_order(self):
        tags = tag_utils.parse_tags("chris, adam, brian")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")

    def test_quotes(self):
        tags = tag_utils.parse_tags('"adam, one"')
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "adam, one")

    def test_quotes_comma_delim(self):
        tags = tag_utils.parse_tags('"adam, one","brian, two","chris, three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam, one")
        self.assertEqual(tags[1], "brian, two")
        self.assertEqual(tags[2], "chris, three")

    def test_quotes_space_delim(self):
        tags = tag_utils.parse_tags('"adam one" "brian two" "chris three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam one")
        self.assertEqual(tags[1], "brian two")
        self.assertEqual(tags[2], "chris three")

    def test_quotes_comma_delim_spaces_ignored(self):
        tags = tag_utils.parse_tags('"adam, one"  ,  "brian, two"  ,  "chris, three"')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam, one")
        self.assertEqual(tags[1], "brian, two")
        self.assertEqual(tags[2], "chris, three")

    def test_quotes_comma_delim_early_wins(self):
        tags = tag_utils.parse_tags('"adam one","brian two" "chris three"')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam one")
        self.assertEqual(tags[1], 'brian two" "chris three')

    def test_quotes_comma_delim_late_wins(self):
        tags = tag_utils.parse_tags('"adam one" "brian two","chris three"')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam one" "brian two')
        self.assertEqual(tags[1], "chris three")

    def test_quotes_comma_delim_late_wins_unescaped_quotes(self):
        "When delimiter changes, return insignificant unescaped quotes"
        tags = tag_utils.parse_tags('adam "one", brian two')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam "one"')
        self.assertEqual(tags[1], "brian two")

    def test_quotes_dont_delimit(self):
        tags = tag_utils.parse_tags('adam"brian,chris dave')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], 'adam"brian')
        self.assertEqual(tags[1], "chris dave")

    def test_quotes_dont_close(self):
        tags = tag_utils.parse_tags('"adam,one","brian,two","chris, dave')
        self.assertEqual(len(tags), 3)
        # Will be sorted, " comes first
        self.assertEqual(tags[0], '"chris, dave')
        self.assertEqual(tags[1], "adam,one")
        self.assertEqual(tags[2], "brian,two")

    def test_quotes_and_unquoted(self):
        tags = tag_utils.parse_tags('adam , "brian, chris" , dave')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian, chris")
        self.assertEqual(tags[2], "dave")

    def test_quotes_order(self):
        tags = tag_utils.parse_tags('chris, "adam", brian')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")

    def test_quotes_escaped(self):
        """
        Tests quotes when delimiter is already comma
        """
        tags = tag_utils.parse_tags('adam, br""ian, ""chris, dave""')
        self.assertEqual(len(tags), 4)
        self.assertEqual(tags[0], '"chris')
        self.assertEqual(tags[1], "adam")
        self.assertEqual(tags[2], 'br"ian')
        self.assertEqual(tags[3], 'dave"')

    def test_quotes_escaped_late(self):
        """
        Tests quotes when delimiter switches to comma
        """
        tags = tag_utils.parse_tags('""adam"" brian"", chris')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], '"adam" brian"')
        self.assertEqual(tags[1], "chris")

    def test_empty_tag(self):
        tags = tag_utils.parse_tags('"adam" , , brian , ')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")

    def test_limit(self):
        with self.assertRaises(ValueError) as cm:
            tag_utils.parse_tags("adam,brian,chris", 1)
        e = cm.exception
        self.assertEqual(str(e), "This field can only have 1 argument")

    def test_limit_quotes(self):
        with self.assertRaises(ValueError) as cm:
            tag_utils.parse_tags('"adam","brian",chris', 2)
        e = cm.exception
        self.assertEqual(str(e), "This field can only have 2 arguments")

    def test_spaces_false_commas(self):
        tags = tag_utils.parse_tags("adam,brian,chris", space_delimiter=False)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")

    def test_spaces_false_spaces(self):
        tags = tag_utils.parse_tags("adam brian chris", space_delimiter=False)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0], "adam brian chris")

    def test_spaces_false_mixed(self):
        tags = tag_utils.parse_tags("adam,brian chris", space_delimiter=False)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian chris")


# ##############################################################################
# ###### utils.render_tags
# ##############################################################################


class UtilsRenderTagsTest(TestCase):
    "Test utils.render_tags"

    def test_simple(self):
        tagstr = tag_utils.render_tags(["adam", "brian", "chris"])
        self.assertEqual(tagstr, "adam, brian, chris")

    def test_escapes_quotes(self):
        tagstr = tag_utils.render_tags(['ad"am', '"brian', 'chris"', '"dave"'])
        self.assertEqual(tagstr, '""brian, ""dave"", ad""am, chris""')

    def test_quotes_commas_and_spaces(self):
        tagstr = tag_utils.render_tags(["adam brian", "chris, dave", "ed"])
        self.assertEqual(tagstr, '"adam brian", "chris, dave", ed')

    def test_parse_renders_tags(self):
        tagstr = "adam, brian, chris"
        tags = tag_utils.parse_tags(tagstr)
        tagstr2 = tag_utils.render_tags(tags)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "adam")
        self.assertEqual(tags[1], "brian")
        self.assertEqual(tags[2], "chris")
        self.assertEqual(tagstr, tagstr2)

    def test_parse_renders_tags_complex(self):
        tagstr = '"""adam brian"", ""chris, dave", "ed, frank", gary'
        tags = tag_utils.parse_tags(tagstr)
        tagstr2 = tag_utils.render_tags(tags)
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], '"adam brian", "chris, dave')
        self.assertEqual(tags[1], "ed, frank")
        self.assertEqual(tags[2], "gary")
        self.assertEqual(tagstr, tagstr2)


# ##############################################################################
# ###### Tree name split and join
# ##############################################################################


class TagTreeSplitUtilTest(TestCase):
    """
    Test split_tree_name
    """

    def test_split_tree_none(self):
        parts = tag_utils.split_tree_name("")
        self.assertEqual(len(parts), 0)

    def test_split_tree_one(self):
        parts = tag_utils.split_tree_name("one")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], "one")

    def test_split_tree_one_single_character(self):
        parts = tag_utils.split_tree_name("o")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], "o")

    def test_split_tree_three(self):
        parts = tag_utils.split_tree_name("one/two/three")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two")
        self.assertEqual(parts[2], "three")

    def test_split_tree_three_last_one_with_single_character(self):
        parts = tag_utils.split_tree_name("one/two/3")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two")
        self.assertEqual(parts[2], "3")

    def test_split_tree_three_spaced(self):
        parts = tag_utils.split_tree_name("  one  /  two  /  three  ")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two")
        self.assertEqual(parts[2], "three")

    def test_split_tree_leading(self):
        parts = tag_utils.split_tree_name("/one")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "")
        self.assertEqual(parts[1], "one")

    def test_split_tree_trailing(self):
        parts = tag_utils.split_tree_name("one/")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "")

    def test_split_tree_escape(self):
        parts = tag_utils.split_tree_name("one/two//dos/three")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two/dos")
        self.assertEqual(parts[2], "three")

    def test_split_tree_escape_odd(self):
        parts = tag_utils.split_tree_name("one/two///three/four")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two/")
        self.assertEqual(parts[2], "three")
        self.assertEqual(parts[3], "four")

    def test_split_tree_escape_even(self):
        parts = tag_utils.split_tree_name("one/two////dos/three")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two//dos")
        self.assertEqual(parts[2], "three")

    def test_split_tree_escape_leading(self):
        parts = tag_utils.split_tree_name("//one/two")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "/one")
        self.assertEqual(parts[1], "two")

    def test_split_tree_escape_trailing(self):
        parts = tag_utils.split_tree_name("one/two//")
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "one")
        self.assertEqual(parts[1], "two/")


class TagTreeJoinUtilTest(TestCase):
    """
    Test join_tree_name
    """

    def test_join_tree_none(self):
        name = tag_utils.join_tree_name([])
        self.assertEqual(name, "")

    def test_join_tree_one(self):
        name = tag_utils.join_tree_name(["one"])
        self.assertEqual(name, "one")

    def test_join_tree_three(self):
        name = tag_utils.join_tree_name(["one", "two", "three"])
        self.assertEqual(name, "one/two/three")

    def test_join_tree_escape(self):
        name = tag_utils.join_tree_name(["one", "two/dos", "three"])
        self.assertEqual(name, "one/two//dos/three")

    def test_join_tree_escape_odd(self):
        name = tag_utils.join_tree_name(["one/", "two"])
        self.assertEqual(name, "one///two")

    def test_join_tree_escape_even(self):
        name = tag_utils.join_tree_name(["one", "two//dos", "three"])
        self.assertEqual(name, "one/two////dos/three")

    def test_join_tree_escape_leading(self):
        name = tag_utils.join_tree_name(["/one", "two"])
        self.assertEqual(name, "//one/two")

    def test_join_tree_escape_trailing(self):
        name = tag_utils.join_tree_name(["one", "two/"])
        self.assertEqual(name, "one/two//")


class TagTreeCleanUtilTest(TestCase):
    """
    Test clean_tree_name
    """

    def test_clean_tree_one(self):
        name = tag_utils.clean_tree_name("one")
        self.assertEqual(name, "one")

    def test_clean_tree_three(self):
        name = tag_utils.clean_tree_name("one/two/three")
        self.assertEqual(name, "one/two/three")

    def test_clean_tree_escape(self):
        name = tag_utils.clean_tree_name("one/two//dos/three")
        self.assertEqual(name, "one/two//dos/three")

    def test_clean_tree_strip(self):
        name = tag_utils.clean_tree_name("  one  /  two  /  three  ")
        self.assertEqual(name, "one/two/three")

    def test_clean_tree_leading(self):
        name = tag_utils.clean_tree_name("/one/two/three")
        self.assertEqual(name, "//one/two/three")

    def test_clean_tree_trailing(self):
        name = tag_utils.clean_tree_name("one/two/three//")
        self.assertEqual(name, "one/two/three//")

    def test_clean_tree_complex(self):
        name = tag_utils.clean_tree_name("/// one / two/ three /")
        self.assertEqual(name, "//// one/two/three //")
