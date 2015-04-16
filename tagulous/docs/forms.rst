.. _forms:

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

Tagulous includes the following adaptors:

Select2, version 3
    The default adaptor, for `Select2 <https://select2.github.io/>`_.

    Autocomplete settings should be a dict, and will be passed to the Select2
    constructor.
    
    Path: ``tagulous/adaptor/select2-3.js``

Selectize
    The adaptor for `Selectize <http://brianreavis.github.io/selectize.js/>`_.
    
    Not yet implemented

jQuery UI autocomplete
    The adaptor for `jQuery UI autocomplete <https://jqueryui.com/autocomplete/>`_.
    
    Not yet implemented


Writing a custom adaptor
~~~~~~~~~~~~~~~~~~~~~~~~

Writing a custom adaptor should be fairly self-explanatory - take a look at the
included adaptors to see how they work. It's mostly just a case of pulling data
out of the HTML field, and fiddling with it a bit to pass it into the library's
constructor.

Tagulous puts certain settings on the HTML field's ``data-`` attribute:

``data-tagulous``
    Always ``true`` - used to identify a tagulous class to JavaScript

``data-tag-type``
    Set to ``single`` when a ``SingleTagField``, otherwise not present.

``data-tag-list``
    JSON-encoded list of tags

``data-tag-url``
    URL to request tags

``data-tag-options``
    JSON-encoded dict of tag options
    
    In addition to the dict from `TagOptions.field_items`_, there will also be:
    
    ``required``
        A boolean indicating whether the form field is required or not

These settings can be used to initialise your autocomplete library of choice.
You should initialise it using ``data-tag-options``'s ``autocomplete_settings``
for default values.

If you write an adaptor which you think would make a good addition to this
project, please do send it in or make a pull request on github - see
`Contributing`_ for more information.


Using form fields without models
--------------------------------

Although in most cases you will want to generate forms with tag fields from a
model with corresponding tag fields, it is possible to use the form fields
directly.

To initialise a ``SingleTagField`` or ``TagField``, you can pass the standard
form field arguments, as well as:

``tag_options``
    A ``TagOptions`` instance. The model-specific options (``protect_all``,
    ``initial`` and ``protect_initial``) will be ignored.

``autocomplete_tags``
    A list of strings of tags. It can actually be any iterable of anything
    which can be converted to a string, so could also be a queryset from a
    ``TagModel`` class, for example.


The ``clean`` methods on these fields returns values suitable for setting on
their corresponding model fields:

``forms.SingleTagField.clean(value)``
    When called on an instance, will return ``None`` if the value is empty,
    or will return a single valid tag as a string.
    
    Note that the ``SingleTagField`` does not allow the character ``"``.

``forms.TagField.clean(value)``
    When called on an instance, will return a sorted list of unique tags, or an
    empty list if there are no tags.

