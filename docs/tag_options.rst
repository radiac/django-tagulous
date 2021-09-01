===========
Tag Options
===========

:ref:`Model options <model_options>` define how a tag model behaves. They can
either be set in the :ref:`model field arguments <model_field_arguments>`, or
in the tag model's :ref:`tagmeta`  class. Once defined, they are then stored in
a :ref:`TagOptions <tagoptions>` instance on the tag model, accessible at
``MyTagModel.tag_options`` (and shared with tag model fields at
``MyTaggedModel.tags.tag_options``).

Tagulous only lets you set options for a tag model in one place - if you use a
custom model you must set options using ``TagMeta``, and if you share an
auto-generated model between fields, only the first field can set options.

:ref:`Form options <form_options>` are a subset of the model options, and are
also used to control tag form fields, and are also stored in a ``TagOptions``
instance. If the field is part of a ``ModelForm`` it will inherit options from
the model, otherwise options can be passed in the field arguments.


.. _model_options:

Model Options
=============

The tag model options are:


.. _option_initial:

``initial``
-----------

List of initial tags for the tag model. Must be loaded into the database
with the management command :ref:`initial_tags <command_initial_tags>`.

Value can be a tag string to be parsed, or an array of strings with one
tag in each string.

To change initial tags, you can change the ``initial`` option and re-run
the command :ref:`initial_tags <command_initial_tags>`.

You should not find that you need to update ``initial`` regularly; if you
do, it would be better to use the Tagulous :doc:`admin tools <admin>` to
add tags to the model directly.

If provided as a tag string, it will be parsed using spaces and commas,
regardless of the :ref:`option_space_delimiter` option.

Default: ``''``


.. _option_protect_initial:

``protect_initial``
-------------------

The ``protected`` state for any tags created by the ``initial`` argument -
see :ref:`protected_tags`.

Default: ``True``


.. _option_protect_all:

``protect_all``
---------------
Whether all tags with count 0 should be protected from automatic deletion.

If false, will be decided by ``tag.protected`` - see :ref:`protected_tags`.

Default: ``False``


.. _option_case_sensitive:

``case_sensitive``
------------------
If ``True``, tags will be case sensitive. For example, ``"django, Django"``
would be two separate tags.

If ``False``, tags will be capitalised according to the first time they are
used.

Note when using sqlite: substring matches on tag names, and matches on
tag names with non-ASCII characters, will never be case sensitive - see the
`databases <https://docs.djangoproject.com/en/dev/ref/databases/#substring-matching-and-case-sensitivity>`_
django documentation for more information.

See also :ref:`option_force_lowercase`

.. note::

    MySQL struggles to offer string case sensitivity at the database level -
    see the `django documentation <https://docs.djangoproject.com/en/dev/ref/databases/#mysql-collation>`_
    for more details. Tagulous therefore offers no formal support for this
    option when running on MySQL - the relevant tests are bypassed, and you
    should assume that ``case_sensitive`` is always ``False``. Patches welcome.

Default: ``False``


.. _option_force_lowercase:

``force_lowercase``
-------------------
Force all tags to lower case

Default: ``False``


.. _option_max_count:

``max_count``
-------------
``TagField`` only - this is not supported by ``SingleTagField``.

Specifies the maximum number of tags allowed.

Set to ``0`` to have no limit.

If you are setting it to ``1``, consider using a ``SingleTagField`` instead.

Default: ``0``


.. _option_space_delimiter:

``space_delimiter``
-------------------
``TagField`` only - this is not supported by ``SingleTagField``.

If ``True``, both commas and spaces can be used to separate tags. If ``False``,
only commas can be used to separate tags.

Default: ``True``


.. _option_tree:

``tree``
--------
Field argument only - this cannot be set in :ref:`tagmeta`

If ``True``, slashes in tag names will be used to denote children, eg
``grandparent/parent/child``, and these relationships can be traversed.
See :doc:`models/tag_trees` for more details.

If ``False``, slashes in tag names will have no significance, and no tree
properties or methods will be present on tag objects.

Default: ``False``


.. _option_autocomplete_initial:

``autocomplete_initial``
------------------------
If ``True``, override all other autocomplete settings and use the tags
defined in the ``initial`` argument for autocompletion, embedded in the
form field HTML.

For more advanced autocomplete filtering options (ie filter tags by user),
see the example :ref:`example_filter_related`.

Default: ``False``


.. _option_autocomplete_view:

``autocomplete_view``
---------------------
Specify the view to use for autocomplete queries.

This should be a value which can be passed to Django's ``reverse()``, eg the
name of the view.

If ``None``, all tags will be embedded into the form field HTML as the
``data-autocomplete`` attribute.

If this is an invalid view, a ``ValueError`` will be raised.

Default: ``None``


.. _option_autocomplete_view_args:

``autocomplete_view_args``
--------------------------
Optional ``args`` passed to the ``autocomplete_view``.

Default: ``None``


.. _option_autocomplete_view_kwargs:

``autocomplete_view_kwargs``
--------------------------
Optional ``kwargs`` passed to the ``autocomplete_view``.

Default: ``None``



.. _option_autocomplete_limit:

``autocomplete_limit``
----------------------
Maximum number of tags to provide at once, when ``autocomplete_view`` is
set.

If the autocomplete adaptor supports pages, this will be the number shown
per page, otherwise any after this limit will not be returned.

If ``0``, there will be no limit and all results will be returned

Default: ``100``


.. _option_autocomplete_view_fulltext:

``autocomplete_view_fulltext``
------------------------------
Whether to perform a start of word match (``__startswith``) or full text match
(``__contains``) in the autocomplete view.

Has no effect if not using ``autocomplete_view``.

Default: ``False`` (start of word)


.. _option_autocomplete_settings:

``autocomplete_settings``
-------------------------
Override the default ``TAGULOUS_AUTOCOMPLETE_SETTINGS``.

For example, the select2 control defaults to use the same width as the form element it
replaces; you can override this by passing their ``width`` option (see their docs on
`appearance <https://select2.org/appearance>`_) as an autocomplete setting::

    myfield = TagField(... autocomplete_settings={"width": "75%"})

Default: ``None``


.. _option_get_absolute_url:

``get_absolute_url``
--------------------
A shortcut for defining a ``get_absolute_url`` method on the tag model.
Only used when defined in tag fields which auto-generate models.

It is common to need to get a URL for a tag, so rather than converting your tag
field to use a custom ``TagModel`` just to implement a ``get_absolute_url``
method, you can pass this argument a callback function.

The callback function will be passed the tag object, and should return the
URL for the tag. See the :ref:`example_tag_url` example for a simple lambda
argument.

If not set, the method ``get_absolute_url`` will not be available and an
``AttributeError`` will be raised.

.. note::
    Due to the way Django migrations freeze model fields, this attribute is not
    available during data migrations. See :ref:`migrations_limitations` for
    more information.

Default: ``None``


.. _option_verbose_name:

``verbose_name_singular``, ``verbose_name_plural``
--------------------------------------------------
When a tag model is auto-generated from a field, it is given a
``verbose_name`` based on the tagged model's name and the tag field's
name; the ``verbose_name_plural`` is the same, but with an added ``s``
at the end. This is primarily used in the admin.

However, this will sometimes not make grammatical sense; these two
arguments can be used to override the field name component of the model
name.

The ``verbose_name_singular`` will usually be used with a ``TagField`` -
for example, the auto-generated model for ``MyModel.tags`` will have the
singular name ``My model tags``; this can be corrected by setting
``verbose_name_singular="tag"`` in the field definition.

The ``verbose_name_plural`` will usually be used with a ``SingleTagField`` -
for example, the auto-generated model for ``MyModel.category`` will have the
plural name ``My model categorys``; this can be corrected by setting
``verbose_name_plural="categories"`` in the field definition.

If one or both of these are not set, Tagulous will try to find the field
name from its ``verbose_name`` argument, falling back to the field name.

.. note::

    When Tagulous automatically generates verbose names, it intentionally
    performs no checks on how long they will be. When Django attempts to create
    permissions for the model, if the generated verbose name is longer than 39
    characters, it may raise a ``ValidationError``. To resolve this, set
    ``verbose_name_singular`` to a string which is 38 characters or less.


.. _form_options:

Form Options
============

The following options are used by form fields:

* :ref:`option_case_sensitive`
* :ref:`option_force_lowercase`
* :ref:`option_max_count`
* :ref:`option_tree`
* :ref:`option_autocomplete_limit`
* :ref:`option_autocomplete_settings`


.. _tagoptions:

The TagOptions Class
====================

The ``TagOptions`` class is a simple container for tag options. The options for
a model field are available from the ``tag_options`` property of unbound
:ref:`model_singletagfield` or :ref:`model_tagfield` fields.

All options listed in :ref:`model_options` are available directly on the
object, except for ``to``. It also provides two instance methods:

``items(with_defaults=True)``
    Get a dict of all options

    If with_defaults is true, any missing settings will be taken from the
    defaults in ``constants.OPTION_DEFAULTS``.

``form_items(with_defaults=True)``
    Get a dict of just the options for a form field.

    If with_defaults is true, any missing settings will be taken from the
    defaults in ``constants.OPTION_DEFAULTS``.

Example::

    initial_tags = MyModel.tags.tag_options.initial
    if "force_lowercase" in MyModel.tags.tag_options.items():
        ...

``TagOptions`` instances can be added together to create a new merged set of
options; note though that this is a shallow merge, ie the value of
``autocomplete_settings`` on the left will be replaced by the value on the
right::

    merged_options = TagOptions(
        autocomplete_settings={'width': 'resolve'}
    ) + TagOptions(
        autocomplete_settings={'allowClear': True}
    )
    # merged_options.autocomplete_settings == {'allowClear': True}

In the same way, setting ``autocomplete_settings`` on the field will replace
any default value.
