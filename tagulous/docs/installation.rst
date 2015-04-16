.. _installation:

Installation
============

Requirements
------------

These packages are required:

* Django => 1.3

These packages are recommended:
* South - to assist with migrations (if Django < 1.7)
* django-compressor - (or similar static asset management library)

Tagulous includes the versions of third party code in its file or path names
to make it easier to track. However, it is highly recommended that you use
something like ``django-compressor`` to compile your scripts into a single file
with a hashed filename, to reduce requests and allow for far-future HTTP
caching.


Installation
------------

1. Install ``django-tagulous`` (currently only on github)::

    pip install -e git+https://github.com/radiac/django-tagulous.git#egg=django-tagulous

   Note: The master branch may sometimes contain minor changes made since the
   version was incremented. These changes will be listed in
   `CHANGES <../CHANGES>`_. It will always be safe to use, but versions will be
   tagged if you only want to follow releases.

2. Add Tagulous to ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'tagulous',
    )

   You may also want to change some settings here (see `Settings`_ below)


You are now ready to add tagulous fields to your models - see
 `Example Usage`_, `Models`_ and `Forms`.


Settings
--------

``TAGULOUS_AUTOCOMPLETE_JS``
    List of paths under ``STATIC_URL`` to any javascript files which are
    required for tagulous autocomplete. These will be added to the form media
    when a tagulous form field is used.
    
    The default list will use the included versions of jQuery and Select2,
    with the tagulous Select2 adaptor. See `Autocomplete Adaptors`_ for
    information about using other included adaptors, or writing your own.
    
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

Model and form fields settings are managed by the `TagOptions`_ class.


Feature flags
~~~~~~~~~~~~~

In most situations Tagulous is able to sprinkle its syntactic sugar in a way
which works alongside Django's darkest magical depths. However, in a few places
Django needs a helping hand to understand the tag fields.

Tagulous can therefore apply some monkey patches to make tag fields operate in
exactly the way you would expect. These patches are written to be as
future-proof as possible, but because this isn't exactly best practice, they
come as optional flags which you can disable using the settings below:

:: _enhancements:

``TAGULOUS_ENHANCE_ALL``
    If ``True``, turns on all enhancements. If ``False``, individual
    enhancement settings apply.
    
    Default: True

``TAGULOUS_ENHANCE_MODEL``
    Django models cannot take ``ManyToManyField`` values in their constructors.
    
    This is the same 

``TAGULOUS_ENHANCE_QUERYSET``
    Tag fields are just sugar-coated ``ForeignKey``s and ``ManyToManyField``s,
    so Django expects them to be tag model instances with primary keys. In most
    cases this doesn't cause a problem, but it does mean that you can't pass
    tag strings to ``QuerySet`` methods such as ``.get()``, ``.filter()`` etc.
    
    When set to ``True``, this will monkey patch ``QuerySet`` to support
    passing tag strings as values for for tag fields. It does this by wrapping
    the original calls; for example, ``.get(title='Mr')`` is essentially
    converted to ``.get(title__name='Mr')``. You can see the changes made in
    ``tagulous.models.queryset``.

    When set to ``False``, the ``QuerySet`` cannot be passed tag strings in
    most cases; ``SingleTagField``s have to be passed an instance or primary
    key like a normal ``ForeignKey``, and ``TagField``s need to be assigned
    afterwards using ``field.add()``, like a normal ``ManyToManyField``.
    
    If set to ``False``, you can still pass custom ``QuerySet`` classes into
    ``tagulous.models.queryset.enhance_queryset()`` to just monkey-patch those.
    
    Default: ``False``, overridden by ``TAGULOUS_ENHANCE_ALL``


Management Commands
-------------------

:: _initial_tags:

initial_tags [<app_name>[.<model_name>[.<field_name>]]]
    Add initial tagulous tags to the database as required
    
    * Tags which are new will be created
    * Tags which have been deleted will be recreated
    * Tags which exist will be untouched
      

