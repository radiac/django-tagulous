===================
Database Migrations
===================

Tagulous supports Django migrations.

Both ``SingleTagField`` and ``TagField`` work in schema and data migrations.
Tagged models will be subclasses of ``TaggedModel`` as normal (as long as
``TAGULOUS_ENHANCE_MODELS`` is ``True``), and tag fields will work as normal.
The only difference is that tag models will be instances of ``BaseTagModel``
and ``BaseTagTreeModel`` rather than their normal non-base versions - but this
is just how migrations work, and it will makes no practical difference.


Adding unique columns
=====================

Migrating a model to a ``TagModel`` or ``TagTreeModel`` involves adding unique fields
(``slug`` and ``path`` for example), which normally requires 3 separate migrations. To
simplify this process, Tagulous provides the helper method ``add_unique_field`` to add
them in a single migration - see step 2 in :ref:`converting_tag_trees` for examples of
their use.

However, use these with care - should part of the function fail for some reason
when using a non-transactional database, it won't be able to roll back and may
be left in an unmigrateable state. It is therefore recommended that you either
make a backup of your database before using this function, or that you follow
the steps in the
`official Django documentation <https://docs.djangoproject.com/en/dev/howto/writing-migrations/#migrations-that-add-unique-fields>`_
to perform the action in 3 separate migrations.


.. _migrations_limitations:

Limitations of Django migrations
================================

Django migrations do not support changing the tag model's base class - for
example, changing a plain model to a ``TagModel``, or a ``TagModel`` to a
``TagTreeModel``). Django migrations have no way to store or apply this change,
so you will need to use the Tagulous helper operation ``ChangeModelBases`` -
see step 3 of :ref:`converting_tag_trees` for more details, or the working
example in
:source:`0003_tree.py <tests/tagulous_tests_migration/django_migrations_expected/0003_tree.py>`.

Django migrations also cannot serialise lambda expressions, so the
``get_absolute_url`` argument is not available during data migrations, neither
when defined on a tag field, nor when in a tag model. If you need to call this
in a data migration, it is recommended that you embed the logic into your
migration.
