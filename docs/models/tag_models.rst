==========
Tag Models
==========

Tags are stored in tag models which subclass :ref:`tagmodel`, and use a
:ref:`tagmodel_manager`. A tag model can either be generated automatically,
or you can create a :ref:`custom model <custom_tag_models>`.

Tags in tag models can be :ref:`protected <protected_tags>` from automatic
deletion when they are not referred to. :ref:`Initial tags <option_initial>`
must be loaded using the :ref:`initial_tags command <command_initial_tags>`.


Tag model classes
=================

.. _tagmodel:

``tagulous.models.TagModel``
----------------------------

A ``TagModel`` subclass has the following fields and methods:


``name``
~~~~~~~~
A ``CharField`` containing the name (string value) of the tag.

Must be unique.


.. _model_slug:

``slug``
~~~~~~~~
A unique ``SlugField``, generated automatically from the name when first
saved.

Slugs will support unicode if the ``TAGULOUS_SLUG_ALLOW_UNICODE``
:ref:`setting <settings>` is ``True``. Empty slugs are not allowed; they will default to
underscore. Slug clashes are avoided by adding an integer to the end.


``count``
~~~~~~~~~
An ``IntegerField`` holding the number of times this tag is in use.


``protected``
~~~~~~~~~~~~~
A ``BooleanField`` indicating whether this tag should be protected from
deletion when the count reaches 0.

It also has several methods primarily for internal use, but some may be useful:


``get_related_objects()``
~~~~~~~~~~~~~~~~~~~~~~~~~
Return a list of instances of other models which refer to this tag; see
the API for more details

``update_count()``
~~~~~~~~~~~~~~~~~~
In case you're doing something weird which causes the count to get out
of sync, call this to update the count, and delete the tag if appropriate.

.. _tagmodel_merge_tags:

``merge_tags(tags)``
~~~~~~~~~~~~~~~~~~~~
Merge the specified tags into this tag.

``tags`` can be a queryset, list of tags or tag names, or a tag string.


.. _tagmodel_manager:

``tagulous.models.TagModelManager``
-----------------------------------

A ``TagModelManager`` is the standard manager for a :ref:`tagmodel`; it is a
subclass of the normal Django model manager, but its queries return a
:ref:`tagmodel_queryset` instead.

It also provides the following additional methods:


``filter_or_initial(...)``
~~~~~~~~~~~~~~~~~~~~~~~~~~
Calls the normal ``filter(...)`` method, but then adds on any initial tags
which may be missing.


.. _queryset_weight:

``weight(min=1, max=6)``
~~~~~~~~~~~~~~~~~~~~~~~~
Annotates a ``weight`` field to the tags. This is a weighted count between
the specified ``min`` and ``max``, which default to ``TAGULOUS_WEIGHT_MIN``
and ``TAGULOUS_WEIGHT_MAX`` (see :ref:`settings`).

This can be used to generate :ref:`tag clouds <tag_clouds>`, for example.


.. _tagmodel_queryset:

``tagulous.models.TagModelQuerySet``
------------------------------------

This is returned by the :ref:`tagmodel_manager`; it is a subclass of the normal
Django ``QuerySet`` class, but implements the same additional methods as the
``TagModelManager``.


.. _custom_tag_models:

Custom Tag Models
=================

A custom tag model should subclass ``tagulous.models.TagModel``, so that
Tagulous can find the fields and methods it expects, and so it uses the
appropriate tag model manager and queryset.

A custom tag model is a normal model in every other way, except it can have a
:ref:`tagmeta` class to define default options for the class.

There is :ref:`an example <example_custom_tag_model>` which illustrates how to
create a custom tag model.

If you want to use tag trees, you will need to subclass
``tagulous.models.TagTreeModel`` instead. The only difference is that
there will be extra fields on the model - see :doc:`tag_trees` for more
details.


.. _tagmeta:

TagMeta
-------

The ``TagMeta`` class is a container for tag options, to be used when creating
a custom tag model.

Set any :ref:`model_options` as class properties. When the model is created by
Python, the options will be available on the tag model class and tag fields
which use it as ``tag_options``.

Tag fields will not be able to override these options, and ``SingleTagField``
fields will ignore ``max_count``.

If ``tree`` is specified, it must be appropriate for the base class of the tag
model, eg if ``tree=True`` the tag model must subclass :ref:`tagtreemodel` -
but if it is not provided it will be set to the correct value.

``TagMeta`` can be inherited, so it can be set on abstract models. Options in
the ``TagMeta`` of a parent model can be overridden by options in the
``TagMeta`` of a child model.

Example::

    import tagulous
    class MyTagModel(tagulous.models.TagModel):
        class TagMeta:
            initial = 'judo, karate'


.. _protected_tags:

Protected tags
==============

The tag model keeps a count of how many times each tag is referenced. When the
tag count reaches ``0``, the tag will be deleted unless its ``protected`` field
is ``True``, or the ``protect_all`` option has been used.

.. note::

    This only happens when the count is updated, ie when the tag is added
    or removed; tags can therefore be created directly on the model with the
    default count of ``0``, ready to be assigned later.


.. _command_initial_tags:

Loading initial tags
====================

Initial tags must be loaded using the ``initial_tags`` management command. You
can either load all initial tags in your site by not passing in any arguments,
or specify an app, model or field to load::

    python manage.py initial_tags [<app_name>[.<model_name>[.<field_name>]]]

* Tags which are new will be created
* Tags which have been deleted will be recreated
* Tags which exist will be untouched
