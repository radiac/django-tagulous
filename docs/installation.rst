============
Installation
============


.. _installation_instructions:

Instructions
============

1. Install ``django-tagulous``::

    pip install django-tagulous


2. In your site settings, add Tagulous to ``INSTALLED_APPS`` and tell Django to use the
   Tagulous serialization modules::

    INSTALLED_APPS = (
        ...
        'tagulous',
    )

    SERIALIZATION_MODULES = {
        'xml':    'tagulous.serializers.xml_serializer',
        'json':   'tagulous.serializers.json',
        'python': 'tagulous.serializers.python',
        'yaml':   'tagulous.serializers.pyyaml',
    }

   There are other global :ref:`settings` you can add here.

3. Add Tagulous fields to your project - see :doc:`models/index`, :doc:`forms` and
   :doc:`usage`.


Remember to run ``manage.py collectstatic`` to collect the JavaScript and CSS resources.

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
    Default max lengths for tag models.

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

``TAGULOUS_SLUG_ALLOW_UNICODE``
    If ``True`` unicode will be allowed in slugs. If ``False`` tag slugs will be forced
    to ASCII.

    As with Django's ``slugify``, this is off by default.

    Default: ``False``

``TAGULOUS_AUTOCOMPLETE_JS``
``TAGULOUS_ADMIN_AUTOCOMPLETE_JS``
    List of static JavaScript files required for Tagulous autocomplete. These will be
    added to the form media when a Tagulous form field is used.

    The order is important: the adaptor must appear last in the list, so that
    it is loaded after its dependencies.

    If you use jQuery elsewhere on your site, you may need to remove `jquery.js` to
    avoid conflicts.

    Default::

        TAGULOUS_AUTOCOMPLETE_JS = (
            "tagulous/lib/jquery.js",
            "tagulous/lib/select2-4/js/select2.full.min.js",
            "tagulous/tagulous.js",
            "tagulous/adaptor/select2-4.js",
        )

``TAGULOUS_AUTOCOMPLETE_CSS``
``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS``
    List of static CSS files required for Tagulous autocomplete. These will be added to
    the form media when a Tagulous form field is used.

    The default list will use the included version of Select2.

    Default::

        TAGULOUS_AUTOCOMPLETE_CSS = {
            'all': ['tagulous/lib/select2-4/css/select2.min.css']
        }

``TAGULOUS_AUTOCOMPLETE_SETTINGS``
    Any settings to pass to the JavaScript via the adaptor. They can be overridden by a
    field's :ref:`autocomplete_settings <option_autocomplete_settings>` option.

    For example, the select2 control defaults to use the same width as the form element
    it replaces; you can override this by passing their ``width`` option (see their docs
    on `appearance <https://select2.org/appearance>`_) as an autocomplete setting::

        TAGULOUS_AUTOCOMPLETE_SETTINGS = {"width": "75%"}

    If set to ``None``, no settings will be passed.

    Default: ``None``

``TAGULOUS_WEIGHT_MIN``
    The default minimum value for the :ref:`weight <queryset_weight>` queryset method.

    Default: ``1``

``TAGULOUS_WEIGHT_MAX``
    The default maximum value for the :ref:`weight <queryset_weight>` queryset method.

    Default: ``6``

``TAGULOUS_ENHANCE_MODELS``
    **Advanced usage** - only use this setting if you know what you're doing.

    Tagulous automatically enhances models, managers and querysets to fully support tag
    fields. This has the theoretical potential for unexpected results, so this setting
    lets the cautious disable this enhancement.

    If you set this to False you will need to manually add Tagulous mixins to your
    models, managers and querysets.

    See :doc:`models/tagged_models` for more information.

    Default: ``True``


System checks
=============

Tagulous adds to the Django system check framework with the following:

``tagulous.W001``
    ``settings.SERIALIZATION_MODULES`` has not been configured as expected

    A common installation error is to forget to set ``SERIALIZATION_MODULES`` as
    described in the :ref:`installation instructions <installation_instructions>`.

    This is a straight string comparison. If your serialisation modules don't match what
    Tagulous is expecting (you're subclassing the Tagulous modules, for example), you
    can disable this warning with the setting::

        SILENCED_SYSTEM_CHECKS = ["tagulous.W001"]


.. _converting_to_tagulous:

Converting to Tagulous
======================

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

   ``django-taggit`` example::

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

   Example::

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
