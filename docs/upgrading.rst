=========
Upgrading
=========

For an overview of what has changed between versions, see the :ref:`changelog`.


Instructions
============

1. Check which version of Tagulous you are upgrading from::

    python
    >>> import tagulous
    >>> tagulous.__version__

2. Upgrade the Tagulous package::

    pip install --upgrade django-tagulous

3. Scroll down to the earliest instructions relevant to your version, and
   follow them up to the latest version.

   For example, to upgrade from 0.8.0, the earliest instructions relevant to
   you are for 0.8.0 or later. 0.7.0 is an earlier version than yours, so you
   don't need to follow those steps.


.. _upgrade_0-11-1

Upgrading from 0.11.1
---------------------

1. Starting with version 0.12.0, Tagulous no longer enforces uniqueness for
   tree ``path`` fields. This means that Django will detect a change to your
   models, and warn you that your migrations are out of sync. It is safe for
   you to create and apply a standard migration with::

        ./manage.py makemigrations
        ./manage.py migrate

   This change is to avoid MySQL (and possibly other databases) from the errror
   ``"BLOB/TEXT column 'path' used in key specification without a key length"``
   - see https://github.com/radiac/django-tagulous/issues/1 for discussion.

2. Version 0.12.0 deprecates the model tag manager's `__len__` method in
   preparation for merging https://github.com/radiac/django-tagulous/pull/10
   to resolve https://github.com/radiac/django-tagulous/issues/9.

   If you are currently using `len(instance.tagfield)` then you should switch
   to using `instance.tagfield.count()` instead.


.. _upgrade_0-9-0:

Upgrading from 0.9.0
--------------------

1. Starting with version 0.10.0, Tagulous is available on pypi. You can
   continue to run the development version direct from github, but if you would
   prefer to use stable releases you can reinstall::

        pip uninstall django-tagulous
        pip install django-tagulous

2. Version 0.10.0 adds ``label`` and ``level`` fields to the ``TagTreeModel``
   base class (they were previously properties). This means that each of your
   tag tree models will need a schema and data migration.

   The schema migration will require a default value for the label; enter any
   valid string, eg ``'.'``

   The data migration will need to call ``mytagtreemodel.objects.rebuild()`` to
   set the correct values for ``label`` and ``level``.

   You will need to create and apply these migrations to each of your tag tree
   models

   Django migrations::

        python manage.py makemigrations myapp
        python manage.py migrate myapp
        python manage.py makemigrations myapp --empty
        # Add data migration operation below
        python manage.py migrate myapp

   Your Django data migration should include::

        def rebuild_tree(apps, schema_editor):
            # For an auto-generated tag tree model:
            model = apps.get_model('myapp', '_Tagulous_MyModel_tagtreefield')

            # For a custom tag tree model:
            #model = apps.get_model('myapp', 'MyTagTreeModel')

            model.objects.rebuild()

        class Migration(migrations.Migration):
            # ... rest of Migration as generated
            operations = [
                migrations.RunPython(rebuild_tree)
            ]


   South migrations::

        python manage.py schemamigration --auto myapp
        python manage.py migrate myapp
        python manage.py datamigration myapp upgrade_trees
        # Add data migration function below
        python manage.py migrate myapp

   Your South data migration function should be::

        def forwards(self, orm):
            # For an auto-generated tag tree model:
            model = orm['myapp._Tagulous_MyModel_tagtreefield'].objects.rebuild()

            # For a custom tag tree model:
            #model = orm['myapp.MyTagTreeModel'].objects.rebuild()

3. Since version 0.10.0 :ref:`option_tree` cannot be set in :ref:`tagmeta`;
   custom tag models must get their tree status from their base class.

4. In version 0.10.0, ``TagOptions.field_items`` was renamed to
   ``TagOptions.form_items``, and ``constants.FIELD_OPTIONS`` was renamed to
   ``constants.FORM_OPTIONS``. These were internal, so should not affect your
   code.

5. The tag parsers now accept a new argument to control whether space is used
   as a delimiter or not. These are internal, so should not affect your code,
   unless you have written a custom adaptor.



.. _upgrade_0-8-0:

Upgrading from 0.8.0
--------------------

1. Since 0.9.0, ``SingleTagField`` and ``TagField`` raise an exception if the
   tag model isn't a subclass of TagModel.

2. The documentation for ``tagulous.models.migrations.add_unique_column`` has
   been clarified to illustrate the risk of using it with a non-transactional
   database. If you use this in your migrations, read the documentation to be
   sure you understand the problem involved.


.. _upgrade_0-7-0:

Upgrading from 0.7.0 or earlier
-------------------------------

1. ``tagulous.admin.tag_model`` was deprecated in 0.8.0 and removed in 0.9.0;
   use ``tagulous.admin.register`` instead::

    tagulous.admin.tag_model(MyModel.tags)
    tagulous.admin.tag_model(MyModel.tags, my_admin_site)
    # becomes:
    tagulous.admin.register(MyModel.tags)
    tagulous.admin.register(MyModel.tags, site=my_admin_site)


2. Since 0.8.0, a ``ValueError`` exception is raised if a tag model field
   definition specifies both a tag model and tag options.

   For custom tag models, tag options must be set by adding a ``class TagMeta``
   to your model. You can no longer set tag options in the tag field.

   Where an auto-generated tag model is shared with another tag field, the
   first tag field must set all tag options.


3. Any existing South migrations with ``SingleTagField`` or ``TagField``
   definitions which automatically generate their tag models will need to be
   manually modified in the ``Migration.models`` definition to have the
   attribute ``'_set_tag_meta': 'True'``. For example, the line::

    'labels': ('tagulous.models.fields.TagField', [], {'force_lowercase': 'True', 'to': u"orm['myapp._Tagulous_MyModel_labels']", 'blank': 'True'}),

   becomes::

    'labels': ('tagulous.models.fields.TagField', [], {'force_lowercase': 'True', 'to': u"orm['myapp._Tagulous_MyModel_labels']", 'blank': 'True', '_set_tag_meta': 'True'}),

   This will use the keyword tag options to update the tag model's objects,
   rather than raising the new ``ValueError``.


.. _changelog:

Changelog
=========

Releases which require special steps when upgrading to them will be marked with
links to the instructions above.

Changes for upcoming releases will be listed without a release date - these
are available by installing the master branch from github (see
:ref:`installation_instructions` for details).


0.12.0, 2017-02-26
------------------

Feature:
* Add Django 1.10 support (fixes #18, #20)

Bugfix:
* Remove ``unique=True`` from tag tree models' ``path`` field (fixes #1)
* Implement slug field truncation (fixes #3)
* Correct MySQL slug clash detection in tag model save
* Correct ``.weight(..)`` to always return floored integers instead of decimals
* Correct max length calculation when adding and removing a value through
  assignment
* `TagDescriptor` now has a `through` attribute to match `ManyToManyDescriptor`

Deprecates:
* `TagField` manager's `__len__` method is now deprecated and will be removed
  in 0.13

Thanks to:
* Pamela McA'Nulty (PamelaM) for MySQL fixes (#1)
* Mary (minidietcoke) for max count fix (#16)
* James Pic (jpic) for documentation corrections (#13)
* Robert Erb (rerb) at AASHE (http://www.aashe.org/) for Django 1.10 support (#18, #20)
* Gaël Utard (gutard) for tag descriptor `through` fix (#19)


0.11.1, 2015-10-05
------------------

Internal:
* Fix package configuration in setup.py


0.11.0, 2015-10-04
------------------

Feature:
* Add support for Python 3.2 to 3.5

Internal:
* Change ``tagulous.models.initial.field_initialise_tags`` and
  ``model_initialise_tags`` to take a file handle as ``report``.


0.10.0, 2015-09-28
------------------
See :ref:`upgrade instructions <upgrade_0-9-0>`

Feature:
* Add fields ``level`` and ``label`` to :ref:`tagtreemodel` (were properties)
* Add ``TagTreeModel.get_siblings()``
* Add :ref:`tagtreemodel_queryset`` methods ``with_ancestors()``,
  ``with_descendants()`` and ``with_siblings()``
* Add :ref:`option_space_delimiter` tag option to disable space as a delimiter
* Tagulous available from pypi as ``django-tagulous``
* :ref:`TagModel.merge_tags <tagmodel_merge_tags>` can now accept a tag string
* :ref:`TagTreeModel.merge_tags <tagtreemodel_merge_tags>` can now merge
  recursively with new argument ``children=True``
* Support for recursively merging tree tags in admin site

Internal:
* Add support for Django 1.9a1
* ``TagTreeModel.tag_options.tree`` will now always be ``True``
* JavaScript ``parseTags`` arguments have changed
* Added example project to github repository

Bugfix:
* ``TagRelatedManager`` instances can be compared to each other
* Admin inlines now correctly suppress popup buttons
* Select2 adaptor correctly parses ajax response
* :ref:`tagmeta` raises an exception if :ref:`option_tree` is set
* Default help text no longer changes for :ref:`model_singletagfield`


0.9.0, 2015-09-14
-----------------
See :ref:`upgrade instructions <upgrade_0-8-0>`

Internal:
* Add support for Django 1.7 and 1.8

Removed:
* ``tagulous.admin.tag_model`` has been removed

Bugfix:
* Using a tag field with a non-tag model raises exception


0.8.0, 2015-08-22
-----------------
See :ref:`upgrade instructions <upgrade_0-7-0>`

Feature:
* Tag cloud support
* Improved admin.register
* Added tag-aware serializers

Deprecated:
* ``tagulous.admin.tag_model`` will be removed in the next version

Bugfix:
* Setting tag options twice raises exception
* Tagged inline formsets work correctly

Internal:
* South migration support improved
* Tests moved to top level, tox support added
* Many small code improvements and bug fixes


0.7.0, 2015-07-01
-----------------

Feature:
* Added tree support


0.6.0, 2015-05-11
-----------------

Feature:
* Initial public preview
