.. _forms:

Forms
=====

Normally tag fields will be used in a ``ModelForm``; they will automatically
use the correct form field and widget to render tag fields with your
selected `autocomplete adaptor <Autocomplete Adaptors>`_.

To save tag fields, just call the ``form.save()`` method as you would normally.
However, because the ``TagField`` is based on a ``ManyToManyField``, if you
call ``form.save(commit=False)`` you will need to call ``form.m2m_save()``
after to save the tags.

See the `ModelForms`_ example for how this works in practice.


Using tag form fields outside model forms
-----------------------------------------

You can also add tag fields to non-model forms, by using
``tagulous.forms.SingleTagField`` and ``tagulous.forms.TagField``. Both fields
accept two new arguments::

``tag_options``
    A `TagOptions`_ instance containing the options for this tag field

``autocomplete_tags``
    An iterable of tags to be embedded for autocomplete. This can either be
    a queryset of tag objects, or a list of tag objects or strings.

A ``SingleTagField`` will return a string containing one tag, and a TagField
will return a list of tags as strings.

See the `Forms without models`_ example for how this works in practice.


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
    
    Path:
        ``tagulous/adaptor/select2-3.js``

    Autocomplete settings should be a dict:
    
    ``defer``
        If ``True``, the tag field will not be initialised automatically; you
        will need to call ``Tagulous.select2(el)`` on it from your own
        javascript. This is useful for fields which are used as templates to
        dynamically generate more.
        
        For example, to use this adaptor with a
        `django-dynamic-formset <https://github.com/elo80ka/django-dynamic-formset>`_
        which uses a ``formTemplate``, set ``{'defer': True}``, then configure
        the formset with::
        
            added: function ($row) {
                Tagulous.select2($row.find('input[data-tagulous]'));
            }
        
        This will need to be clear or set to ``False`` in the admin settings.
    
    ``width``
        This is the same as in Select2's documentation, but the Tagulous
        default is ``resolve`` instead of ``off``, for the best chance of
        working without complication.
    
    All other settings will be passed to the Select2 constructor.
    
Planned for future releases:

* `Selectize <http://brianreavis.github.io/selectize.js/>`_.
* `jQuery UI autocomplete <https://jqueryui.com/autocomplete/>`_.


Filtering autocomplete tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default the autocomplete values will list all tags. However, you will often
only want to show the initial tags, or tags which the current user has used,
or tags which have been used in conjunction with another field on your model.

Because model tag fields are normal Django relationships, you can filter
embedded autocomplete tags by overriding the form's ``__init__`` method. To
filter an ajax autocomplete view, wrap ``tagulous.views.autocomplete`` in your
own view function which filters for you.

For examples of these approaches, see
`Filtering autocomplete by related fields`_.


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
    JSON-encoded list of tags.

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


Creating an inline formset of tagged models for a tag
-----------------------------------------------------

In most cases Tagulous works with Django's default inline model formsets.
However, there is a specific case where it doesn't: when you create an inline
formset using tagged models with a tag as the parent model (eg when you edit
a tag and its corresponding instances of the tagged model).

In this specific case, you must use the formset class
``tagulous.forms.TaggedInlineFormSet``. For example:

    class Person(models.Model):
        name = models.CharField(max_length=255)
        title = tagulous.models.SingleTagField(initial='Mr, Mrs')

    PersonInline = forms.models.inlineformset_factory(
        Person.title.tag_model,
        Person,
        formset=tagulous.forms.TaggedInlineFormSet,
    )

This would allow you to generate a formset for all ``Person``s using a specific
``title`` tag.

Tagulous will automatically apply this fix in the admin site, as long as the
tag admin class is registered using ``tagulous.admin.register``.

Without the ``TaggedInlineFormSet`` class in this situation, the tag count will
be incorrect when adding tagged model instances, and editing will fail because
the default formset will try to use the tag name as a primary key.

The ``TaggedInlineFormSet`` class will only perform actions under this specific
relationship, so is safe to use in other situations.

