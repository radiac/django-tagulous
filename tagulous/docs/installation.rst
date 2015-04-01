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

If you want to use tagulous constants, remember to have ``from tagulous import constants as tagulous_contants`` at the top of your settings.

``TAGULOUS_AUTOCOMPLETE_JS``
    List of paths under ``STATIC_URL`` to any javascript files which are
    required for tagulous autocomplete. These will be added to the form media
    when a tagulous form field is used.
    
    The default list will use the included versions of jQuery and Select2,
    with the tagulous Select2 adaptor. See `Autocomplete Adaptors`_ for
    information about using other included adaptors, or writing your own.
    
    If you want to use included files, it is advised that you use the values in
    ``constants.py``, so that when you upgrade Tagulous any paths to third
    party code will by updated too.
    
    Default: ``[tagulous_contants.PATH_JQUERY, tagulous_contants.PATH_SELECT2_JS, tagulous_contants.PATH_SELECT2_ADAPTOR]``

``TAGULOUS_AUTOCOMPLETE_CSS``
    List of paths under ``STATIC_URL`` to any CSS files which are required for
    tagulous autocomplete. These will be added to the form media when a
    tagulous form field is used.
    
    The default list will use the included version of Select2. As with
    javascript files it is advised that you use the values in ``constants.py``.
    
    Default: ``[tagulous_contants.PATH_SELECT2_CSS]``

``TAGULOUS_AUTOCOMPLETE_SETTINGS``
    Any settings which you want to override in the default adaptor. These will
    be converted to a JSON value and embedded in the HTML field's
    ``data-tagulous-settings`` attribute. They can be overridden by a field's
    ``autocomplete_settings`` option.
    
    Default: ``{}``

``TAGULOUS_ADMIN_AUTOCOMPLETE_JS``
    List of paths under ``STATIC_URL`` to any javascript files which are
    required for the admin site. This lets you configure your public and admin
    sites separately if you need to.
    
    By default this will be the same as you have set for
    ``TAGULOUS_AUTOCOMPLETE_JS``.
    
    Default: ``TAGULOUS_AUTOCOMPLETE_JS``

``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS``
    List of paths under ``STATIC_URL`` to any CSS files which are required for
    the admin site. This lets you configure your public and admin sites
    separately if you need to.
    
    By default this will be the same as you have set for
    ``TAGULOUS_AUTOCOMPLETE_CSS``.
    
    Default: ``TAGULOUS_AUTOCOMPLETE_CSS``

``TAGULOUS_ADMIN_AUTOCOMPLETE_SETTINGS``
    Admin settings for overriding the adaptor defaults.
    
    By default this will be the same as you have set for
    ``TAGULOUS_AUTOCOMPLETE_SETTINGS``.
    
    Default: ``TAGULOUS_AUTOCOMPLETE_SETTINGS``


Management Commands
-------------------

:: _initial_tags:

initial_tags [<app_name>[.<model_name>[.<field_name>]]]
    Add initial tagulous tags to the database as required
    
    * Tags which are new will be created
    * Tags which have been deleted will be recreated
    * Tags which exist will be untouched
      

