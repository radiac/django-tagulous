=================
Tag String Parser
=================

Tagulous model and form fields accept a tag string value - a list of tag names
separated by spaces or commas::

    # These will parse to 'run', 'jump', 'hop'
    'run jump hop'
    'run,jump,hop'

If the tag string contains both spaces and commas, commas take priority. Spaces
at the start or end of a tag name are ignored by the parser::

    # These will parse to 'run', 'shot put', 'hop'
    # This is also how Tagulous will render these tags
    'run, shot put, hop'

If a tag name contains a space or a comma it should be escaped by quote marks
for clarity, and will be when Tagulous renders the tag string::

    # This is how Tagulous will render 'run', 'shot put'
    'run, "shot put"'

Again, quoted tag names can be separated by spaces or commas, and commas take
priority::

    # These will parse to 'run', 'shot put', 'hop'
    'run "shot put" hop'
    'run,"shot put",hop'

    # But this will parse to 'run "shot put"' 'hop'
    'run "shot put", hop'

If the tag model is a :doc:`tree <models/tag_trees>`, the tag name is the full
path, which is split on the ``/`` character into a path of tag nodes; the tag
label is the final part of the path. The parser ignores a single slash if it
is escaped with another, ie ``slash//escaped``.

If the tag field has :ref:`option_space_delimiter` set to ``False`` then only
commas will be used to separate tags.

The parser is implemented in both Python and JavaScript for consistency.

For more examples and how the parser treats odd edge cases, see the examples
used for testing the parser in :source:`tests/test_utils.py` and
:source:`tests/spec/javascripts/tagulous.spec.js`.


Using the parser directly
=========================

Normally Tagulous uses the parser automatically behind the scenes when needed;
however, there may be times when you need to parse or render tag strings
manually - for example, when :ref:`converting_to_tagulous` or
:ref:`custom_autocomplete_adaptor`.


.. _python_parser:

In Python
---------

The python parser can be found in ``tagulous.utils``:

``tag_names = tagulous.utils.parse_tags(tag_string, max_count=0, space_delimiter=True)``
    Given a tag string, returns a sorted list of unique tag names.

    The parser does not attempt to enforce :ref:`option_force_lowercase` or
    :ref:`option_case_sensitive` options - these should be applied before and
    after parsing, respectively.

    The optional ``max_count`` argument defaults to ``0``, which means no
    limit. For any other value, if more tags are returned than specified, the
    parser will raise a ``ValueError``.

    The optional ``space_delimiter`` argument defaults to ``True``, to allow
    either spaces or commas to be used as deliminaters to separate the tags,
    with priority for commas. If ``False``, only commas will be used as the
    delimiter.

``tag_string = tagulous.utils.render_tags(tag_names)``
    Given a list of tags or tag names, generate a tag string.

``node_labels = tagulous.utils.split_tree_name(tag_name)``
    Given a tree tag name, split it on valid ``/`` characters into a list of
    labels for each node in the tag's path.

``tag_name = tagulous.utils.join_tree_name(parts)``
    Given a list of node labels, return a tree tag name.


.. _javascript_parser:

In JavaScript
-------------

The JavaScript parser will normally be automatically added to the page by tag
fields, as one of the scripts in ``TAGULOUS_AUTOCOMPLETE_JS``
(see :ref:`settings`). However, if for some reason you want to use it without a
tag field, you can add it to your page manually with::

    <script src="{% static "tagulous/tagulous.js %}"></script>

The parser adds the global variable ``Tagulous``:

``tagNames = Tagulous.parseTags(tagString, spaceDelimiter=true, withRaw=false)``
    Given a tag string, returns a sorted list of unique tag names

    If ``spaceDelimiter=false``, only commas will be used to separate tag
    names. If it is unset or true, spaces are used as well as commas.

    The option ``withRaw=true`` is intended for use when parsing live input;
    the function will instead return ``[tags, raws]``,  where ``tags`` is a
    list of tags which is unsorted and not unique, and ``raws`` is a list of
    raw strings which were left after the corresponding entry in ``tags`` was
    parsed. For example::

        var result = Tagulous.parseTags('one,two,three', true, true),
            tags = result[0],
            raws = parsed[1];
        tags === ['one', 'two', 'three'];
        raws === ['two,three', 'three', null];

    If the last tag is not explicitly ended with a delimiter, the corresponding
    item in ``raws`` will be ``null`` instead of an empty string, to indicate
    that the parser unexpectedly ran out of characters.

    This is useful when parsing live input if the last item in ``raws`` is an
    empty string the tag has bee closed; if it is ``null`` then the tag is
    still being entered.

``tagString = Tagulous.renderTags(tagNames)``
    Given a list of tag names, generate a tag string.

