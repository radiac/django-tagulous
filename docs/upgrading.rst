=========
Upgrading
=========

Instructions
============

1. Check which version of Tagulous you are upgrading from::

    python
    >>> import yarr
    >>> tagulous.__version__

2. Upgrade the Tagulous package::

    pip install -e git+https://github.com/radiac/django-tagulous.git#egg=django-tagulous

3. Scroll down to the earliest instructions relevant to your version, and
   follow them up to the latest version.
   
   For example, to upgrade from 0.8.0, the earliest instructions relevant to
   you are for 0.8.0 or later. 0.7.0 is an earlier version than yours, so you
   don't need to follow those steps.


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

Releases which require special steps when upgrading to them will be marked.
Changes for upcoming releases will be listed without a release date - these
are available by installing the master branch from github.


0.9.0, 2015-09-14
-----------------

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
