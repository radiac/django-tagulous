=========
Changelog
=========

Tagulous follows semantic versioning in the format ``BREAKING.FEATURE.BUG``:

* ``BREAKING`` will be marked with links to the details and upgrade instructions in
  :doc:`upgrading`.
* ``FEATURE`` and ``BUG`` releases will be safe to install without reading the upgrade
  notes.

Changes for upcoming releases will be listed without a release date - these
are available by installing the develop branch from github.


1.3.1, 2021-12-21
-----------------

Changes:

* Switch to pytest and enforce linting


Bugfix:

* Fix ``_filter_or_exclude`` exception missed by tests (#144, #149)


Thanks to:

* nschlemm for the ``_filter_or_exclude" fix (#144, #149)


1.3.0, 2021-09-07
-----------------

Features:

* Add ``similarly_tagged`` to tagged model querysets, and ``get_similar_objects`` to
  instantiated tag fields (#115)
* New DRF serializer to serialize tags as strings (#111)
* Initial ``TagField`` values passed on ``Form(initial=...)`` can now be a string, list
  or tuple of strings or tags, or queryset (#107)
* Add system check for ``settings.SERIALIZATION_MODULES`` (#101)

Bugfix:

* Fix incorrect arguments for the TagField's ``RelatedManager.set``
* Upgrade select2 to fix composed characters (#138)
* Fix select2 input where quotes in quoted tags could be escaped
* The select2 control is applied when the formset:added event adds a tag field (#97)
* Fix edge case circular import (#124)


Thanks to:

* valentijnscholten for the form ``initial=`` solution (#107)


1.2.1, 2021-08-31
-----------------

Bugfix:

* Fix issue with update_or_create (#135)


1.2.0, 2021-08-25
-----------------

Upgrade notes: :ref:`upgrade_1-1-0`

Features:

* Django 3.2 support
* Option ``autocomplete_view_fulltext`` for full text search in autocomplete view (#102)

Changes:

* Slugification now uses standard Django for unicode for consistency
* Add ``autocomplete_view_args`` and ``autocomplete_view_kwargs`` options (#119, #120)
* Documentation updates (#105, #113, #131)
* Fix division by zero issue in ``weight()`` (#102)

Bugfix:

* Fix issue where the Select2 adaptor for SingleTagField didn't provide an empty value,
  which meant it would look like it had defaulted to a value which wasn't set. (#116)
* Fix issue where the Select2 adaptor didn't correctly handle the ``required``
  attribute, which meant browser field validation would fail silently. (#116)
* Fix dark mode support in Django admin (#125)
* Fix collapsed select2 in Django admin (#123)
* Fix duplicate migration issue (#93)
* Tagged models can now be pickled (#109)

Thanks to:

* BoPeng for the ``autocomplete_view_args`` config options
* valentijnscholten for the select2 doc fix
* Jens Diemer (jedie) for the readme update
* dany-nonstop for ``autocomplete_view_fulltext`` and weight division issue
* poolpoolpoolpool for form.media docs (#131)


1.1.0, 2020-12-06
-----------------

Feature:

* Add Django 3.0 and 3.1 support (#85)

Changes:

* Drops support for Python 2 and 3.5
* Drops support for Django 1.11 and earlier
* Drops support for South migrations

Bugfix:

* Resolves ``ManyToManyRel`` issue sometimes seen in loaddata (#110)

Thanks to:

* Diego Ubirajara (dubirajara) for ``FieldDoesNotExist`` fix for Django 3.1
* Andrew O'Brien (marxide) for ``admin.helpers`` fix for Django 3.1


1.0.0, 2020-10-08
-----------------

Upgrade notes: :ref:`upgrade_0-14-1`

Feature:

* Added adaptor for Select2 v4 and set as default for Django 2.2+ (#11, #12, #90)
* Support full unicode slugs with new ``TAGULOUS_SLUG_ALLOW_UNICODE`` setting (#22)


Changes:

* Drops support for Django 1.8 and earlier


Bugfix:

* Tag fields work with abstract and concrete inheritance (#8)
* Ensure weighted values are integers not floats (#69, #70)
* The admin site in Django 2.2+ now uses the Django vendored versions of jQuery and
  select2 (#76)
* Fix support for single character tags in trees (#82)
* Fix documentation for adding registering tagged models in admin (#83)
* Fix division by zero in weight() (#59, #61)
* Fix support for capitalised table name in PostgreSQL (#60, #61)
* Tag fields are stripped before parsing, preventing whitespace tags in SingleTagFields
  (#29)
* Fix documentation for quickstart (#41)
* Fix ``prefetch_related()`` on tag fields (#42)
* Correctly raise an ``IntegrityError`` when saving a tree tag without a name (#50)


Internal:

* Signals have been refactored to global handlers (instead of multiple independent
  handlers bound to descriptors)
* Code linting improved; project now uses black and isort, and flake8 pases


Thanks to:

* Khoa Pham (phamk) for ``prefetch_related()`` fix (#42, #87)
* Erik Van Kelst (4levels) for division by zero and capitalised table fixes (#60, #61,
  #62)
* hagsteel for weighted values fix (#69, #70)
* Michael Röttger (mcrot) for single character tag fix (#81, #82)
* Frank Lanitz (frlan) for admin documentation fix (#83)


0.14.1, 2019-09-04
------------------

Upgrade notes: :ref:`upgrade_0-14-0`

Feature:

* Add Django 2.2 support (closes #71)
* Upgrade example project to Django 2.2 on Python 3.7


Bugfix:

* Correct issue with multiple databases (#72)


Thanks to:

* Dmitry Ivanchenko (ivanchenkodmitry) for multiple database fix (#72)


0.14.0, 2019-02-24
------------------

Feature:

* Add Django 2.0 support (fixes #48, #65)
* Add Django 2.1 support (fixes #56, #58)


Bugfix:

* Fix example project (fixes #64)


Thanks to:

* Diego Ubirajara (dubirajara) for Widget.render() fix (#58)


0.13.2, 2018-05-28
------------------

Feature:

* Tag fields now support the argument :ref:`argument_to_base`


0.13.1, 2018-05-19
------------------

Upgrade notes: :ref:`upgrade_0-13-0`

Bugfix:

* ``TagField(null=...)`` now raises a warning about the ``TagField``, rather than the
  parent ``ManyToManyField``.


Changes:

* Reduce support for Python 3.3


0.13.0, 2018-04-30
------------------

Upgrade notes: :ref:`upgrade_0-12-0`

Feature:

* Add Django 1.11 support (fixes #28)


Changes:

* Reduce support for Django 1.4 and Python 3.2
* Remove deprecated ``TagField`` manager's ``__len__`` (#10, fixes #9)


Bugfix:

* Fix failed search in select2 v3 widget when pasting multiple tags (fixes #26)
* Fix potential race condition when creating new tags (#31)
* Temporarily disabled some migration tests which only failed under Python 2.7 with
  Django 1.9+ due to logic issues in the tests.
* Fix deserialization exception for model with ``ManyToOneRel`` (fixes #14)


Thanks to:

* Martín R. Guerrero (slackmart) for removing ``__len__`` method (#9, #10)
* Mark London for select2 v3 widget fix when pasting tags (#26)
* Peter Baumgartner (ipmb) for fixing race condition (#31)
* Raniere Silva (rgaics) for fixing deserialization exeption (#14, #45)


0.12.0, 2017-02-26
------------------

Upgrade notes: :ref:`upgrade_0-11-1`

Feature:

* Add Django 1.10 support (fixes #18, #20)

Bugfix:

* Remove ``unique=True`` from tag tree models' ``path`` field (fixes #1)
* Implement slug field truncation (fixes #3)
* Correct MySQL slug clash detection in tag model save
* Correct ``.weight(..)`` to always return floored integers instead of decimals
* Correct max length calculation when adding and removing a value through assignment
* `TagDescriptor` now has a `through` attribute to match `ManyToManyDescriptor`

Deprecates:

* `TagField` manager's `__len__` method is now deprecated and will be removed in 0.13


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

* Change ``tagulous.models.initial.field_initialise_tags`` and ``model_initialise_tags``
  to take a file handle as ``report``.


0.10.0, 2015-09-28
------------------

Upgrade notes: :ref:`upgrade_0-9-0`

Feature:

* Add fields ``level`` and ``label`` to :ref:`tagtreemodel` (were properties)
* Add ``TagTreeModel.get_siblings()``
* Add :ref:`tagtreemodel_queryset` methods ``with_ancestors()``,
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

Upgrade notes: :ref:`upgrade_0-8-0`

Internal:

* Add support for Django 1.7 and 1.8


Removed:

* ``tagulous.admin.tag_model`` has been removed


Bugfix:

* Using a tag field with a non-tag model raises exception


0.8.0, 2015-08-22
-----------------

Upgrade notes: :ref:`upgrade_0-7-0`

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
