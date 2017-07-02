============
Installation
============

Requirements
============

These packages are required:

* `Django <https://www.djangoproject.com/>`_ 1.4.2 to 1.11, on Python 2.7 and
  3.3 to 3.6.

These packages are recommended, but optional:

* `unidecode <https://pypi.python.org/pypi/Unidecode>`_
* `django-compressor <https://github.com/django-compressor/django-compressor>`_
  or similar, to optimise static files
* `South <https://pypi.python.org/pypi/South>`_ 1.0.2 or later, to manage
  database migrations (if using Django 1.6 or earlier)

If you are replacing an existing tagging solution, follow the
:ref:`installation_instructions`, then read :ref:`converting_to_tagulous`.


.. _installation_instructions:

Instructions
============

1. Install ``django-tagulous``::

    pip install django-tagulous

   or to install with improved unicode support in slugs (installs ``unidecode``
   - see :ref:`model_slug` for more details)::

    pip install django-tagulous[i18n]

   .. note::
        If you prefer, you can also install the development version direct from
        github::

            pip install -e git+https://github.com/radiac/django-tagulous.git@develop#egg=django-tagulous

        This may contain changes made since the last version was released -
        these will be listed in the :ref:`changelog`.

        If you are planning to contribute to Tagulous, you may want to install
        with the ``dev`` extra requirements - see :doc:`contributing` for more
        details.

2. In your site settings, add Tagulous to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'tagulous',
    )

   In the same file, tell Django to use the Tagulous serialization modules, so
   that Django can serialize tag fields (for fixtures etc)::

    SERIALIZATION_MODULES = {
        'xml':    'tagulous.serializers.xml_serializer',
        'json':   'tagulous.serializers.json',
        'python': 'tagulous.serializers.python',
        'yaml':   'tagulous.serializers.pyyaml',
    }

   You may also want to change some Tagulous settings here - see the global
   max length :ref:`settings` for details.

You are now ready to add Tagulous fields to your models - see
:doc:`models/index`, :doc:`forms` and :doc:`usage`.

When you want to upgrade your Tagulous installation in the future, check
:doc:`upgrading` to see if there are any special actions that you need to take.

.. note::
    If you use MySQL there are some limitations you should be aware of - see:

    * the :ref:`setting <settings>` for max length for limitations of maximum
      tag lengths
    * the tag option :ref:`option_case_sensitive` for limitations of case
      sensitivity.


.. _settings:

Settings
========

.. note::
    Model and form field options are managed separately by :doc:`tag_options`.

``TAGULOUS_NAME_MAX_LENGTH``
``TAGULOUS_SLUG_MAX_LENGTH``
``TAGULOUS_LABEL_MAX_LENGTH``
    Default max length for tag models.

    .. note::

        When MySQL is using utf8mb4 charset, all unique fields have a
        max-length of 191 characters, because MySQL max key length in 767
        bytes and utf8mb4 reserves 4 bytes per character, thus 767/4 = 191.

        If you use MySQL, we therefore recommend the following settings:

            TAGULOUS_NAME_MAX_LENGTH=191

    Default::

        TAGULOUS_NAME_MAX_LENGTH = 255
        TAGULOUS_SLUG_MAX_LENGTH = 50
        TAGULOUS_LABEL_MAX_LENGTH = TAGULOUS_NAME_MAX_LENGTH

``TAGULOUS_SLUG_TRUNCATE_UNIQUE``
    Number of characters to allow for the numerical suffix when finding a
    unique slug, ie if set to 5, the slug will be truncated by up to 5
    characters to allow for a suffix of up to `_9999`.

    Default: ``5``

``TAGULOUS_AUTOCOMPLETE_JS``
    List of paths under ``STATIC_URL`` for any JavaScript files which are
    required for Tagulous autocomplete. These will be added to the form media
    when a Tagulous form field is used.

    The default list will use the included versions of jQuery and Select2,
    with the tagulous Select2 adaptor. See :ref:`autocomplete_adaptors` for
    information about using other adaptors, or writing your own.

    The order is important: the adaptor must appear last in the list, so that
    it is loaded after its dependencies.

    Because a typical Tagulous installation will use multiple JavaScript files,
    you may want to use something like
    `django-compressor <http://django-compressor.readthedocs.org/en/latest/>`_
    to combine them into a single file to optimise requests.

    Default::

        TAGULOUS_AUTOCOMPLETE_JS = (
            'tagulous/lib/jquery.js',
            'tagulous/lib/select2-3/select2.min.js',
            'tagulous/tagulous.js',
            'tagulous/adaptor/select2.js',
        )

``TAGULOUS_AUTOCOMPLETE_CSS``
    List of paths under ``STATIC_URL`` to any CSS files which are required for
    tagulous autocomplete. These will be added to the form media when a
    tagulous form field is used.

    The default list will use the included version of Select2.

    Default::

        TAGULOUS_AUTOCOMPLETE_CSS = {
            'all': ['tagulous/lib/select2-3/select2.css']
        }

``TAGULOUS_AUTOCOMPLETE_SETTINGS``
    Any settings which you want to override in the default adaptor. These will
    be converted to a JSON value and embedded in the HTML field's
    ``data-tag-options`` attribute. They can be overridden by a field's
    :ref:`autocomplete_settings <option_autocomplete_settings>` option.

    If set to ``None``, no settings will be added to the HTML field.

    Default: ``None``

``TAGULOUS_ADMIN_AUTOCOMPLETE_JS``
    List of paths under ``STATIC_URL`` to any javascript files which are
    required for the admin site. This lets you configure your public and admin
    sites separately if you need to.

    If your autocomplete library uses jQuery and you want to use the Django
    admin's version, you will need to set ``window.jQuery = django.jQuery;``
    before loading the autocomplete javascript.

    By default this will be the same as you have set for
    ``TAGULOUS_AUTOCOMPLETE_JS``.

    Default: value of setting ``TAGULOUS_AUTOCOMPLETE_JS``

``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS``
    List of paths under ``STATIC_URL`` to any CSS files which are required for
    the admin site. This lets you configure your public and admin sites
    separately if you need to.

    By default this will be the same as you have set for
    ``TAGULOUS_AUTOCOMPLETE_CSS``.

    Default: value of setting ``TAGULOUS_AUTOCOMPLETE_CSS``

``TAGULOUS_ADMIN_AUTOCOMPLETE_SETTINGS``
    Admin settings for overriding the adaptor defaults.

    By default this will be the same as you have set for
    ``TAGULOUS_AUTOCOMPLETE_SETTINGS``.

    Default: value of setting ``TAGULOUS_AUTOCOMPLETE_SETTINGS``

``TAGULOUS_ENHANCE_MODELS``
    Feature flag to automatically enhance models, managers and querysets to
    fully support tag fields.

    In most situations Tagulous is able to sprinkle its syntactic sugar without
    intefering with third-party code. However, there are a few places in
    Django's darkest magical depths of its model code that it needs a helping
    hand to understand the tag fields. When this setting is ``True``, any
    models which use tag fields will automatically be enhanced to make this
    happen, along with their managers and querysets.

    If you set this to ``False``, Tagulous will still work, but certain
    aspects may not work as you would expect - you should consider manually
    enhancing your models, managers and querysets.

    See :doc:`models/tagged_models` for more information.

    Default: ``True``

``TAGULOUS_WEIGHT_MIN``
    The default minimum value for the :ref:`weight <queryset_weight>` queryset
    method.

    Default: ``1``

``TAGULOUS_WEIGHT_MAX``
    The default maximum value for the :ref:`weight <queryset_weight>` queryset
    method.

    Default: ``6``



.. _converting_to_tagulous:

Converting to Tagulous
----------------------

If you're already using a tagging library which you'd like to replace with
Tagulous, freeze the tags into a temporary column, remove the old tagging code,
add a new tagulous TagField, then copy the tags back across.

.. warning::
    This hasn't been tested with your data, so back up your database first,
    just in case.

1. Create a schema migration to add a ``TextField`` to your tagged
   model, where we'll temporarily store the tags for that instance.

   ``django-taggit`` example::

        class MyModel(models.Model):
            ...
            tags = TaggableManager()
            tags_store = models.TextField(blank=True)

   ``django-tagging`` example::

        class MyModel(models.Model):
            ...
            tags_store = models.TextField(blank=True)
        tagging.register(MyModel)

2. Create a data migration to copy the tags into the new field as a
   string.

   ``django-taggit`` example using South::

        def forwards(self, orm):
            import tagulous
            for obj in orm['myapp.MyModel'].objects.all():
                obj.tags_store = tagulous.utils.render_tags(obj.tags.all())

   ``django-taggit`` example using Django migrations::

        def store_tags(apps, schema_editor):
            import tagulous
            model = apps.get_model('myapp', 'MyModel')
            for obj in model.objects.all():
                obj.tags_store = tagulous.utils.render_tags(obj.tags.all())

        class Migration(migrations.Migration):
            operations = [
                migrations.RunPython(store_tags)
            ]

   The example for ``django-tagging`` would be the same, only replace
   ``obj.tags.all()`` with ``obj.tags``.

3. Remove the old tagging code from your model, and create a schema migration
   to clean up any unused fields or models.

4. Add a ``TagField`` to your tagged model and create a schema migration::

        import tagulous
        class MyModel(models.Model):
            tags = tagulous.models.TagField()
            tags_store = models.TextField(blank=True)

   Be careful to set appropriate arguments, ie ``blank=True`` if some of your
   ``tags_store`` fields may be empty.

5. Create a data migration to copy the tags into the new field.

   Example using South::

        def forwards(self, orm):
            for obj in orm['myapp.MyModel'].objects.all():
                obj.tags = obj.tags_store
                obj.tags.save()

   Example using Django migrations::

        def load_tags(apps, schema_editor):
            model = apps.get_model('myapp', 'MyModel')
            for obj in model.objects.all():
                obj.tags = obj.tags_store
                obj.tags.save()

        class Migration(migrations.Migration):
            operations = [
                migrations.RunPython(load_tags)
            ]

6. Create a schema migration to remove the temporary tag storage field
   (``tag_store`` in these examples)

7. Apply the migrations and start using tagulous
