"""
Based almost entirely on Alex Gaynor's django-taggit
https://github.com/alex/django-taggit/

In turn that is ported from Jonathan Buchanan's django-tagging
http://django-tagging.googlecode.com
"""

from django.conf import settings as global_settings
from django.utils.encoding import force_unicode
from django.utils.functional import wraps

from tagulous import settings

def parse_tags(tag_string, max_count=0):
    """
    Parses tag input, with multiple word input being activated and
    delineated by commas and double quotes. Quotes take precedence, so
    they may contain commas.

    Returns a sorted list of unique tag names.
    """
    if not tag_string:
        return []

    tag_string = force_unicode(tag_string)

    # Special case - if there are no commas or double quotes in the
    # input, we don't *do* a recall... I mean, we know we only need to
    # split on spaces.
    if u',' not in tag_string and u'"' not in tag_string:
        words = list(set(split_strip(tag_string, u' ')))
        words.sort()
        return words

    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there are
    # any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(tag_string)
    try:
        while True:
            c = i.next()
            if c == u'"':
                if buffer:
                    to_be_split.append(u''.join(buffer))
                    buffer = []
                # Find the matching quote
                open_quote = True
                c = i.next()
                while c != u'"':
                    buffer.append(c)
                    c = i.next()
                if buffer:
                    word = u''.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == u',':
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer as unquoted.
        if buffer:
            if open_quote and u',' in buffer:
                saw_loose_comma = True
            to_be_split.append(u''.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = u','
        else:
            delimiter = u' '
        for chunk in to_be_split:
            words.extend(split_strip(chunk, delimiter))
    words = list(set(words))
    words.sort()
    
    # Check the count
    if max_count and len(words) > max_count:
        raise ValueError('This field can only have %s argument%s'
            % (max_count, '' if max_count == 1 else 's')
        )
    
    return words

def split_strip(string, delimiter=u','):
    """
    Splits ``string`` on ``delimiter``, stripping each resulting string
    and returning a list of non-empty strings.
    """
    if not string:
        return []

    words = [w.strip() for w in string.split(delimiter)]
    return [w for w in words if w]


def edit_string_for_tags(tags):
    """
    Given list of ``Tag`` instances, creates a string representation of
    the list suitable for editing by the user, such that submitting the
    given string representation back without changing it will give the
    same list of tags.

    Tag names which contain commas will be double quoted.

    If any tag name which isn't being quoted contains whitespace, the
    resulting string of tag names will be comma-delimited, otherwise
    it will be space-delimited.
    """
    names = []
    for tag in tags:
        # This will catch a list of Tag objects or tag name strings
        name = u'%s' % tag
        if u',' in name or u' ' in name:
            names.append(u'"%s"' % name)
        else:
            names.append(name)
    return u', '.join(sorted(names))


def get_setting(setting):
    """
    Helper function to get a setting from global settings, or tagulous defaults
    """
    if hasattr(global_settings, setting):
        return getattr(global_settings, setting)
    if hasattr(settings, setting):
        return getattr(settings, setting)
    raise ValueError("Invalid setting %s" % setting)
    