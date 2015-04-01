Forms
=====

Because this is based on a ManyToManyField, if you call `.save(commit=False)`
(eg your form consists of formsets), remember to call `.m2m_save()` after
to save the tags.

If you have a straight form, `.m2m_save()` will be called automatically so you
don't need to do anything else.

The JavaScript code requires jQuery 1.7 or later. For convenience there is a
bundled copy of jQuery in the tagulous static directory. This is included in
public pages by default, but can be turned off by changing the
TAGULOUS_PUBLIC_JQUERY setting to ``False``.


Autocomplete Adaptors
---------------------

Tagulous uses a javascript files it calls an ``adaptor`` to apply your chosen
autocomplete library to the Tagulous form field.

Only Select2 is included with Tagulous; if you want to use a different library,
you will need to add it to your project's static files, and add the relative
path under ``STATIC_URL`` to the appropriate ``TAGULOUS_`` settings.

The included adaptors have their path names stored in ``constants.py``:

``PATH_SELECT2_ADAPTOR``
    The default adaptor for `Select2 <https://select2.github.io/>`_.

``PATH_CHOSEN_ADAPTOR``
    The adaptor for `chosen <http://harvesthq.github.io/chosen/>`_.

``PATH_SELECTIZE_ADAPTOR``
    The adaptor for `selectize.js <http://brianreavis.github.io/selectize.js/>`_.

``PATH_JQUERYUI_ADAPTOR``
    The adaptor for `jQuery UI autocomplete <https://jqueryui.com/autocomplete/>`_.


Writing a custom adaptor
~~~~~~~~~~~~~~~~~~~~~~~~

Writing a custom adaptor should be fairly self-explanatory - take a look at the
included adaptors to see how they work.

Tagulous puts certain settings on the HTML field's ``data-`` attribute:

``data-tag-autocomplete``
    JSON-encoded list of tags

``data-tag-autocomplete-url``
    URL to request tags

``data-tag-options``
    JSON-encoded dict of tag options

These settings can be used to initialise your autocomplete library of choice.
You should initialise it using ``data-tag-options``'s ``autocomplete_settings``
for default values.
