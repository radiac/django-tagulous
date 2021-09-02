=========
Upgrading
=========

This document details breaking changes between versions, with any necessary steps to
safely upgrade.

For an overview of what has changed between versions, see the :doc:`changelog`.


Instructions
============

Tagulous follows semantic versioning in the format ``BREAKING.FEATURE.BUG``:

* Read the upgrade notes for a ``BREAKING`` release to see if you need to take
  further action when upgrading.
* ``FEATURE`` and ``BUG`` releases will be safe to install without reading the upgrade
  notes.

1. Check which version of Tagulous you are upgrading from::

    python
    >>> import tagulous
    >>> tagulous.__version__

2. Upgrade the Tagulous package::

    pip install --upgrade django-tagulous

3. Scroll down to the earliest instructions relevant to your version, and
   follow them up to the latest version.


.. _upgrade_1-1-0:

Upgrading from 1.1.0
---------------------

Slugify behaviour
~~~~~~~~~~~~~~~~~

In Tagulous 1.2.0 the slugify logic has been replaced with Django's now all supported
Django versions support the ``allow_unicode`` slugify option.

If unicode tag slugs are not enabled with ``TAGULOUS_SLUG_ALLOW_UNICODE``
:ref:`setting <settings>`, Django's implementation of unicode to ASCII does not support
logographic characters, so these will be stripped as per Django's standard ``slugify()``
output, rather than Tagulous' old behaviour of replacing them with underscore
characters. This can now lead to empty slugs, which will now default to a single
underscore.

As a result of this change, the optional dependency ``unidecode`` and its corresponding
extra installation requirements ``[i18n]`` have been removed.


.. _upgrade_0-14-1:

Upgrading from 0.14.1
---------------------

Django and Python support
~~~~~~~~~~~~~~~~~~~~~~~~~

Tagulous 0.14.1 was the last version to support Django 1.10 and earlier.
Tagulous 1.0.0 requires Django 1.11 or later, and Python 2.7 or 3.5 or later.


Autocomplete upgrade
~~~~~~~~~~~~~~~~~~~~

Tagulous 1.0.0 changes the default JavaScript adaptor to use select2 v4. This may
necessitate some styling changes on your user-facing pages if you have overridden the
default styles.


Single tag behaviour
~~~~~~~~~~~~~~~~~~~~

Tagulous 1.0.0 no longer allows whitespace tags in ``SingleTagField``.


.. _upgrade_0-14-0:

Upgrading from 0.14.0
---------------------

Tagulous 0.14.0 was the last version to officially support Django 1.10 or
earlier.


.. _upgrade_0-13-0:

Upgrading from 0.13.0
---------------------

1. Setting ``null`` in a model ``TagField`` has raised a warning in the
   parent ``ManyToManyField`` since Django 1.9. The warning now correctly
   blames a ``TagField`` instead. The ``null`` argument in a model ``TagField``
   is deprecated and has no effect, so should not be used.

2. Version 0.13.1 reduces support for Python 3.3. No known breaking changes
   have been introduced, but this version of Python will no longer be tested
   against due to lack of support in third party tools.


.. _upgrade_0-12-0:

Upgrading from 0.12.0
---------------------

1. Auto-generated tag models have been renamed.

   Django 1.11 introduced a rule that models cannot start with an underscore.
   Prior to this, Tagulous auto-generated tag models started ``_Tagulous_``, to
   indicate they are auto-generated. From now on, they will start
   ``Tagulous_``.

   Django migrations should detect this model name change::

        ./manage.py makemigrations
        Did you rename the myapp._Tagulous_MyModel model to Tagulous_MyModel? [y/N]

   Answer `y` for all Tagulous auto-generated models, and migrate::

        ./manage.py migrate

   Troubleshooting:

   * If you do not see the rename prompt when running ``makemigrations``, you
     will need to edit the migration manually - see
     `RenameModel <https://docs.djangoproject.com/en/1.11/ref/migration-operations/#renamemodel>`
     in the Django documentation for more details.
   * If any ``AlterField`` changes to the ``SingleTagField`` or ``TagField``
     definitions are included in this set of migrations, the new tag model's
     name will not be correctly detected and you will see the errors
     ``Related model ... cannot be resolved`` or ``AttributeError: 'TagField'
     object has no attribute 'm2m_reverse_field_name'``. To resolve these,
     manually change the ``to`` parameter in your ``AlterField``'s tag field definition from ``myapp._Tagulous_...`` to ``myapp.Tagulous_...``.
   * If you see an error ``Renaming the table while in a transaction is not supported
     because it would break referential integrity``, add ``atomic = False`` to your
     migration class.

2. Version 0.13.0 reduces support for Django 1.4 and Python 3.2. No known
   breaking changes have been introduced, but these versions of Django and
   Python will no longer be tested against due to lack of support in third
   party tools.

3. The ``TagField`` manager's ``__len__`` has now been removed, following its
   deprecation in 0.12.0. If you are currently using ``len(instance.tagfield)``
   then you should switch to using ``instance.tagfield.count()`` instead (see
   :ref:`upgrade instructions <upgrade_0-11-1>`).


.. _upgrade_0-11-1:

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

   Any `db.add_column` calls will need to be changed too::

    db.add_column(u'myapp_mymodel', 'singletag',
                  self.gf('tagulous.models.fields.SingleTagField')(null=True, ...),
                  ...)

   becomes::

    db.add_column(u'myapp_mymodel', 'singletag',
                  self.gf('tagulous.models.fields.SingleTagField')(_set_tag_meta=True, null=True, ...),
                  ...)

   This will use the keyword tag options to update the tag model's objects,
   rather than raising the new ``ValueError``.
