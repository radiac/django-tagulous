=========
Tag Trees
=========

Tags can be nested using tag trees for detailed categorisation, with tags
having parents, children and siblings.

Tags in tag trees denote parents using the forward slash character (``/``). For
example, ``Animal/Mammal/Cat`` is a ``Cat`` with a parent of ``Mammal`` and
grandparent of ``Animal``.

To use a slash in a tag name, escape it with a second slash; for example the
tag name ``Animal/Vegetable`` can be entered as ``Animal//Vegetable``.

A custom tag tree model must be a subclass of :ref:`tagtreemodel` instead of
the normal :ref:`tagmodel`; for automatically-generated tag models, this is
managed by setting the :ref:`option_tree` field option to ``True``.

Tag Tree Model Classes
======================

.. _tagtreemodel:

``tagulous.models.TagTreeModel``
--------------------------------

Because tree tag names are fully qualified (include all ancestors) and unique,
there is no difference to normal tags in how they are set or compared.

A ``TagTreeModel`` subclasses :ref:`tagmodel`; it inherits all the normal
fields and methods, and adds the following:

.. note::
    Field values are computed and set automatically in the ``save()`` method -
    so don't try to use them until the tag has been saved.


``parent``
~~~~~~~~~~
A ``ForeignKey`` to the parent tag. Tagulous sets this automatically when
saving, creating missing ancestors as needed.


``children``
~~~~~~~~~~~~
The reverse relation manager for ``parent``, eg ``mytag.children.all()``.


``label``
~~~~~~~~~
A ``CharField`` containing the name of the tag without its ancestors.

Example: a tag named ``Animal/Mammal/Cat`` has the label ``Cat``


``slug``
~~~~~~~~
A ``SlugField`` containing the slug for the tag label.

Example: a tag named ``Animal/Mammal/Cat`` has the slug ``cat``


.. _model_path:

``path``
~~~~~~~~
A ``TextField`` containing the path for this tag - this slug, plus all ancestor
slugs, separated by the ``/`` character, suitable for use in URLs. Tagulous
sets this automatically when saving.

Example: a tag named ``Animal/Mammal/Cat`` has the path ``animal/mammal/cat``


``level``
~~~~~~~~~
An ``IntegerField`` containing the level of this tag in the tree (starting from
1).


.. _tagtreemodel_merge_tags:

``merge_tags(tags, children=False)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Merge the specified tags into this tag.

``tags`` can be a queryset, list of tags or tag names, or a tag string.

If ``children=False``, only the specified tags will be merged; tagged items
will be reassigned to this tag, but if there are child tags they will not be
touched. If child tags do exist, although the merged tags' counts will be 0,
they will not be cleared.

If ``children=True``, child tags will be merged into children of this tag,
retaining structure; eg merging ``Pet`` into ``Animal`` will merge
``Pet/Mammal`` into ``Animal/Mammal``, ``Pet/Mammal/Cat`` into
``Animal/Mammal/Cat`` etc. Tags will be created if they don't exist.


``get_ancestors()``
~~~~~~~~~~~~~~~~~~~
Returns a queryset of all ancestors, ordered by level.

``get_descendants()``
~~~~~~~~~~~~~~~~~~~~~
Returns a queryset of all descendants, ordered by level.

``get_siblings()``
~~~~~~~~~~~~~~~~~~~~~
Returns a queryset of all siblings, ordered by name.

This includes the node itself; if you don't want it in the results, exclude it
afterwards, eg::

    siblings = node.get_siblings().exclude(pk=node.pk)


.. _tagtreemodel_manager:

``tagulous.models.TagTreeModelManager``
---------------------------------------

A ``TagTreeModelManager`` is the standard manager for a :ref:`tagtreemodel`; it
is a subclass of :ref:`tagmodel_manager` so provides those methods, but its
queries return a :ref:`tagtreemodel_queryset` instead.


.. _tagtreemodel_queryset:

``tagulous.models.TagTreeModelQuerySet``
----------------------------------------

This is returned by the :ref:`tagtreemodel_manager`; it is a subclass of
:ref:`tagmodel_queryset` so provides those methods, but also:

``with_ancestors()``
~~~~~~~~~~~~~~~~~~~~

Returns a new queryset containing the nodes from the calling queryset, plus
their ancestor nodes.

``with_descendants()``
~~~~~~~~~~~~~~~~~~~~~~

Returns a new queryset containing the nodes from the calling queryset, plus
their descendant nodes.

``with_siblings()``
~~~~~~~~~~~~~~~~~~~

Returns a new queryset containing the nodes from the calling queryset, plus
theirm sibling nodes.




.. _converting_tag_trees:

Converting from to tree tags from normal tags
=============================================

When converting from a normal tag model to a tag tree model, you will need to
add extra fields. One of those (``path``) is a unique field, which means extra
steps are needed to build the migration.

These instructions will convert an existing ``TagModel`` to a ``TagTreeModel``.
Look through the code snippets and change the app and model names as
required:

1. Create a data migration to escape the tag names.

   You can skip this step if you have been using slashes in normal tags and
   want them to be converted to nested tree nodes.

   When using Django migrations, run ``manage.py makemigrations myapp --empty``
   and add::

    def escape_tag_names(apps, schema_editor):
        model = apps.get_model('myapp', 'Tagulous_MyModel_Tags')
        for tag in model.objects.all():
            tag.name = tag.name.replace('/', '//')
            tag.save()
    operations = RunPython(escape_tag_names)

   With South, run ``manage.py datamigration myapp escape_tags`` and add::

    def forwards(self, orm):
        for tag in orm['myapp.Tagulous_MyModel_tags'].objects.all():
            tag.name = tag.name.replace('/', '//')
            tag.save()

2. Create a schema migration to change the model fields. Because paths are not
   allowed to be null, you need to add the ``path`` field as a non-unique
   field, set some unique data on it (such as the object's ``pk``), and then
   change the field to add back the unique constraint.

   To do this reliably on all database types, see
   `Migrations that add unique fields <https://docs.djangoproject.com/en/1.8/howto/writing-migrations/#migrations-that-add-unique-fields>`_
   in the official Django documentation.

   If you are only working with databases which support transactions, you can
   use a tagulous helper to add the unique field:

   1. When you create the migration, Django or South will prompt you for a
      default value for the unique ``path`` field; answer with ``'x'`` (do the
      same for the ``label`` field when asked).

      Change the new migration to use the Tagulous helper to add the ``path``
      field.

   2. When using Django migrations::

        from django.utils import six
        import tagulous.models.migrations
        ...

        class Migration(migrations.Migration):
            # ... rest of Migration as generated
            operations = [
                ...
                # Leave other operations as they are, just replace AddField:
            ] + tagulous.models.migration.add_unique_field(
                model_name='_tagulous_mymodel_tags',
                name='path',
                field=models.TextField(unique=True),
                preserve_default=False,
                set_fn=lambda obj: setattr(obj, 'path', six.text_type(obj.pk)),
            ) + [
                ...
            ]

      With South::

        def forwards(self, orm):
            ...

            # Leave other migration statements as they are - just replace the
            # call to db.add_column for the path field with add_unique_column.
            # Replace ``myapp`` with your app name, and
            # replace ``Tagulous_MyModel_tags`` with your tag model name

            from tagulous.models.migrations import add_unique_column
            from django.utils import six

            # Adding field 'Tagulous_MyModel_tags.path'
            add_unique_column(
                self, db, orm['myapp.Tagulous_MyModel_tags'], 'path',
                lambda obj: setattr(obj, 'path', six.text_type(obj.pk)),
                'django.db.models.fields.TextField',
            )

    .. warning::
        Although ``add_unique_column`` and ``add_unique_field`` do work with
        non-transactional databases, it is not without risk. See
        :doc:`migrations` for more details.

3. Skip this step if you are using South.

   We have changed the abstract base class of the tag model, but Django
   migrations have no native way to do this. You will need to use the Tagulous
   helper operation ``ChangeModelBases`` to do it manually, otherwise future
   data migrations will think it is a ``TagModel``, not a ``TagTreeModel``.

   Modify the migration from step 2; if you followed the official Django
   documentation and have several migrations, modify the last one. Add the
   ``ChangeModelBases`` to the end of your ``operations`` list, as the last
   operation::

        import tagulous.models.migrations

        class Migration(migrations.Migration):
            # ... rest of Migration as generated
            operations = [
                # ... rest of operations
                tagulous.models.migrations.ChangeModelBases(
                    name='_tagulous_mymodel_tags',
                    bases=(tagulous.models.models.BaseTagTreeModel, models.Model),
                )
            ]

4. Create another data migration to rebuild the tag model and set the paths.

   When using Django migrations::

        def rebuild_tag_model(apps, schema_editor):
            model = apps.get_model('myapp', 'Tagulous_MyModel_Tags')
            model.objects.rebuild()
        operations = RunPython(rebuild_tag_model)

   With South::

        def forwards(self, orm):
            orm['myapp.Tagulous_MyModel_tags'].objects.rebuild()

   If you skipped step 1, this will also create and set parent tags as
   necessary.

5. Run the migrations

You can see a working migration using steps 2 and 3 in the Tagulous tests, for
:source:`Django migrations <tests/tagulous_tests_migration/django_migrations_expected/0003_tree.py>`
and
:source:`South migrations <tests/tagulous_tests_migration/south_migrations_expected/0003_tree.py>`.
