.. _installation:

Installation
============

Requirements
------------

These packages are required:

* Django => 1.4

These packages are recommended, but optional:

* unidecode
* South, to assist with migrations (if Django < 1.7)

Tagulous has been tested under Python 2.7.

If you are replacing an existing tagging solution, follow the `Installation`_
instructions, then read `Converting to Tagulous`_.


Installation
------------

1. Install ``django-tagulous`` (currently only on github)::

    pip install -e git+https://github.com/radiac/django-tagulous.git#egg=django-tagulous

   There are also optional extras - sets of dependencies which you can ask pip
   to install by adding them to the end of the package name. They are:
   
   * ``i18n``, for improved unicode support in slugs (``unidecode``) - see
     `slugs <_model_slug>`_ for more details.
   * ``dev``, for testing (``tox`` and ``jasmine``) - see `Contributing`_ for
     more details.
   
   Example of installing with extras::
   
    pip install -e git+https://github.com/radiac/django-tagulous.git#egg=django-tagulous[i18n][dev]

   Note: The master branch may sometimes contain minor changes made since the
   version was incremented. These changes will be listed in
   `CHANGES <../CHANGES>`_. It will always be safe to use, but versions will be
   tagged if you only want to follow releases.

2. In your site settings, add Tagulous to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'tagulous',
    )
   
   In the same file, tell Django to use the Tagulous serialization modules, so
   that Django can serialize tag fields (for fixtures etc):
   
    SERIALIZATION_MODULES = {
        'xml':    'tagulous.serializers.xml_serializer',
        'json':   'tagulous.serializers.json',
        'python': 'tagulous.serializers.python',
        'yaml':   'tagulous.serializers.pyyaml',
    }

   You may also want to change some Tagulous settings here - see `Settings`_
   below.

You are now ready to add Tagulous fields to your models - see
`Example Usage`_, `Models`_ and `Forms`_.


Settings
--------

Note: model and form fields settings are managed by the `TagOptions`_ class.

``TAGULOUS_AUTOCOMPLETE_JS``
    List of paths under ``STATIC_URL`` to any javascript files which are
    required for tagulous autocomplete. These will be added to the form media
    when a tagulous form field is used.
    
    The default list will use the included versions of jQuery and Select2,
    with the tagulous Select2 adaptor. See `Autocomplete Adaptors`_ for
    information about using other included adaptors, or writing your own.
    
    The order is important: the adaptor must appear last in the list, so it is
    loaded after its dependencies.
    
    Because a typical Tagulous installation will use multiple JavaScript files,
    you may want to use something like
    `django-compressor <http://django-compressor.readthedocs.org/en/latest/>`_
    to combine them into a single file to optimise requests.
    
    Default::
    
        ('tagulous/lib/jquery.js',
        'tagulous/lib/select2-3/select2.min.js',
        'tagulous/tagulous.js',
        'tagulous/adaptor/select2.js')

``TAGULOUS_AUTOCOMPLETE_CSS``
    List of paths under ``STATIC_URL`` to any CSS files which are required for
    tagulous autocomplete. These will be added to the form media when a
    tagulous form field is used.
    
    The default list will use the included version of Select2.
    
    Default: ``{'all':  ['tagulous/lib/select2-3/select2.css']}``

``TAGULOUS_AUTOCOMPLETE_SETTINGS``
    Any settings which you want to override in the default adaptor. These will
    be converted to a JSON value and embedded in the HTML field's
    ``data-tag-options`` attribute. They can be overridden by a field's
    ``autocomplete_settings`` option.
    
    See `Autocomplete Adaptors`_ for accepted values for this setting.
    
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
    
    See `Working with tagged models`_ for more information.
    
    Default: ``True``

``TAGULOUS_WEIGHT_MIN``
    The default minimum value for the `weight <_queryset_weight>`_ queryset
    method.
    
    Default: ``1``

``TAGULOUS_WEIGHT_MAX``
    The default maximum value for the `weight <_queryset_weight>`_ queryset
    method.
    
    Default: ``6``


Management Commands
-------------------

.. _initial_tags:

initial_tags [<app_name>[.<model_name>[.<field_name>]]]
    Add initial tagulous tags to the database as required
    
    * Tags which are new will be created
    * Tags which have been deleted will be recreated
    * Tags which exist will be untouched
      

Converting to Tagulous
----------------------

If you're already using a tagging library which you'd like to replace with
Tagulous, freeze the tags into a temporary column, remove the old tagging code,
add a new tagulous TagField, then copy the tags back across.

**Warning:** this hasn't been tested with your data, so back up your database
first, just in case.

1. Create a schema migration to add a ``TextField`` to your tagged
   model, where we'll temporarily store the tags for that instance.
   
   Example for ``django-taggit``::

    class MyModel(models.Model):
        ...
        tags = TaggableManager()
        tags_store = models.TextField(blank=True)

   Example for ``django-tagging``::
   
    class MyModel(models.Model):
        ...
        tags_store = models.TextField(blank=True)
    tagging.register(MyModel)

2. Create a data migration to copy the tags into the new field as a
   string.
   
   Example using South for ``django-taggit``::

    import tagulous
    for obj in orm['myapp.MyModel'].objects.all():
        obj.tags_store = tagulous.utils.render_tags(obj.tags.all())

   Example using South for ``django-tagging``::
   
    import tagulous
    for obj in orm['myapp.MyModel'].objects.all():
        obj.tags_store = tagulous.utils.render_tags(obj.tags)

3. Remove the old tagging code from your model, and create a schema migration
   to clean up any unused fields or models.

4. Create a schema migration to add a ``TagField`` to your tagged model::
   
    import tagulous
    class MyModel(models.Model):
        tags = tagulous.models.TagField()
        tags_store = models.TextField(blank=True)

   Be careful to set appropriate arguments, ie ``blank=True`` if some of your
   ``tags_store`` fields may be empty.

5. Create a data migration to copy the tags into the new field.

   Example using South::

    for obj in orm['myapp.MyModel'].objects.all():
        obj.tags = obj.tags_store

6. Create a schema migration to remove the temporary tag storage field
   (``tag_store`` in these examples)

7. Apply the migrations and start using tagulous
