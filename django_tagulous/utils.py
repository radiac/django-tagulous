"""
Tag parsing and printing

Loosely based on django-taggit and django-tagging
"""

from django.utils.encoding import force_str

from .constants import COMMA, DOUBLE_QUOTE, QUOTE, SPACE, TREE

# ##############################################################################
# ###### Tag name parse and render
# ##############################################################################


def parse_tags(tag_string: str, max_count=0, space_delimiter=True) -> list[str]:
    """
    Tag parser

    Rules without quotes:
        If a comma is present it's used as the delimiter
        Otherwise space is used as the delimiter
        Spaces at the start and end of tags are ignored

    Rules with quotes
        Quotes can be escaped by double quotes, ie ""
        Commas outside quotes take precedence over spaces as delimiter
        Unmatched quotes will be left in the string

    If space_delimiter is False, space will never be used as a delimiter.

    Tree tags can be further split into their parts with split_tree_name
    """
    # Empty string easiest case
    if not tag_string:
        return []

    tag_string = force_str(tag_string)

    # Prep variables for the parser
    tags = []
    tag = ""
    delimiter = SPACE
    in_quote = None
    chars = False

    # Disable spaces
    if not space_delimiter:
        delimiter = COMMA

    # Bypass main parser for efficiency if no quotes
    if QUOTE not in tag_string:
        # No quotes - simple split and strip

        # Normally split on commas
        delimiter = COMMA

        # But if no commas, split on spaces
        if COMMA not in tag_string and space_delimiter:
            delimiter = SPACE

        # Split and strip tags
        tags = split_strip(tag_string, delimiter)

    else:
        # Break tag string into list of (index, char)
        chars = list(enumerate(tag_string))

    # Loop through chars
    while chars:
        index, char = chars.pop(0)

        # See if it's a delimiter
        if not in_quote:
            # Comma delimiter takes priority
            if delimiter != COMMA and char == COMMA:
                delimiter = COMMA

                # All previous tags were actually just one tag
                tag = tag_string[0:index].strip()
                tags = []

                # Strip start/end quotes
                tag_len = len(tag)
                tag = tag.lstrip(QUOTE)
                left_quote_count = tag_len - len(tag)
                tag_len = len(tag)
                tag = tag.rstrip(QUOTE)
                right_quote_count = tag_len - len(tag)

                # Escape inner quotes
                tag = tag.replace(DOUBLE_QUOTE, QUOTE)

                # Add back escaped start/end quotes
                tag = (
                    (QUOTE * int(left_quote_count / 2))
                    + tag
                    + (QUOTE * int(right_quote_count / 2))
                )

                # Add back insignificant unescaped quotes.
                #
                # There are only two scenarios where there can be unescaped
                # quotes at the start, followed by a comma later:
                #   1. The comma is quoted - but that means in_quote is True,
                #      in which case we won't be in this code branch
                #   2. The comma comes after a matching closing unescaped quote
                #
                # Therefore there can't be insigificant unescaped quotes on the
                # left and unescaped quotes on the right are only insignificant
                # if there are no unescaped quotes on the left
                if right_quote_count % 2 == 1 and left_quote_count % 2 == 0:
                    tag += QUOTE

            # Found end of tag
            if char == delimiter:
                tag = tag.rstrip()
                if tag:
                    tags.append(tag)
                    tag = ""
                # Following tested manually due to coverage bug
                #   See https://bitbucket.org/ned/coveragepy/issues/198
                continue  # pragma: no cover

            # If tag is empty, ignore whitespace
            if not tag and char == SPACE:
                continue

        # Now either in a quote, or not a delimiter
        # If it's not a quote, add to tag
        if char != QUOTE:
            tag += char
            continue

        # Char is quote - count how many quotes appear here
        quote_count = 1
        while chars and chars[0][1] == QUOTE:
            quote_count += 1
            chars.pop(0)

        if not tag:
            # Quote at start
            # If an odd number, now in quote
            if quote_count % 2 == 1:
                in_quote = True

            # Tag starts with escaped quotes
            tag = QUOTE * int(quote_count / 2)
        else:
            # Quote in middle or at end
            # Add any escaped
            tag += QUOTE * int(quote_count / 2)

            # An odd number followed by a delimiter will mean it has ended
            # Need to look ahead to figure it out
            if quote_count % 2 == 1:
                # If it's the last character, it has closed
                if len(chars) == 0:
                    in_quote = False
                    break

                for i2, c2 in chars:
                    if c2 == SPACE:
                        if delimiter == SPACE:
                            # Quotes closed; tag will end next loop
                            in_quote = False
                            break
                        else:
                            # Spaces are insignificant during whitespace
                            # Tag may continue, keep checking chars
                            # Following tested manually due to coverage bug
                            continue  # pragma: no cover
                    elif c2 == COMMA:
                        # Quotes closed; tag will end next loop
                        # Delimiter doesn't matter, comma always wins
                        in_quote = False
                        break

                    # Tag has not ended
                    # Add odd quote to tag and keep building
                    tag += QUOTE
                    break

    # Chars expended
    if tag:
        # Partial tag remains; add to stack
        if in_quote:
            # Add the quote back to the start - it wasn't significant after all
            tag = QUOTE + tag
        tags.append(tag)

    # Enforce uniqueness and sort
    tags = list(set(tags))
    tags.sort()

    # Check the count
    if max_count and len(tags) > max_count:
        raise ValueError(
            "This field can only have %s argument%s"
            % (max_count, "" if max_count == 1 else "s")
        )

    return tags


def split_strip(string, delimiter=","):
    """
    Splits ``string`` on ``delimiter``, stripping each resulting string
    and returning a list of non-empty strings.
    """
    if not string:
        return []

    words = [w.strip() for w in string.split(delimiter)]
    return [w for w in words if w]


def render_tags(tags):
    """
    Creates a tag string from a list of Tag instances or strings, suitable for
    editing.

    Tag names which contain commas will be quoted, existing quotes will be
    escaped.
    """
    names = []
    for tag in tags:
        # This will catch a list of Tag objects or tag name strings
        name = str(tag)

        name = name.replace(QUOTE, DOUBLE_QUOTE)
        if COMMA in name or SPACE in name:
            names.append('"%s"' % name)
        else:
            names.append(name)
    return ", ".join(sorted(names))


# ##############################################################################
# ###### Tree name split and join
# ##############################################################################


def split_tree_name(name):
    """
    Split a tree tag name into its parts

    A slash can be escaped by double slash, ie //
    """
    name = name.strip()
    if len(name) == 0:
        return []

    # Replace escaped slashes with escape char, split on remaining slashes
    ESCAPE_CHAR = "\0"
    escaped = name.replace(TREE + TREE, ESCAPE_CHAR)
    return [x.strip().replace(ESCAPE_CHAR, TREE) for x in escaped.split(TREE)]


def join_tree_name(parts):
    """
    Join tree tag name parts into a single name string

    A slash in a part will be escaped by double slash, ie //
    """
    return TREE.join(part.replace(TREE, TREE + TREE) for part in parts)


def clean_tree_name(name):
    """
    Make sure a tree name is valid

    * Escapes leading or trailing slashes
    * Strips leading and trailing whitespace around parts
    """
    # Count the number of slashes, ensure it's even (all escaped)
    left = len(name) - len(name.lstrip(TREE))
    if left % 2 == 1:
        name = TREE + name

    right = len(name) - len(name.rstrip(TREE))
    if right % 2 == 1:
        name += TREE

    # Split and join to strip whitespace
    return join_tree_name(split_tree_name(name))
