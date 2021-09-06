=====
Forms
=====

Normally tag fields will be used in a ``ModelForm``; they will automatically
use the correct form field and widget to render tag fields with your
selected :ref:`autocomplete adaptor <autocomplete_adaptors>`.

To save tag fields, just call the ``form.save()`` method as you would normally.
However, because :ref:`model_tagfield` is based on a ``ManyToManyField``, if
you call ``form.save(commit=False)`` you will need to call ``form.m2m_save()``
after to save the tags.

See the :ref:`example_modelform` example for how this works in practice.



Form field classes
==================

You can also use Tagulous form fields outside model forms by using the
:ref:`form_singletagfield` and :ref:`form_tagfield` form fields - see the
:ref:`example_form` example for how this works in practice.

Tag forms fields take standard `Django core field arguments <https://docs.djangoproject.com/en/dev/ref/forms/fields/#core-field-arguments>`_
such as ``label`` and ``required``.


.. _form_singletagfield:

``tagulous.forms.SingleTagField``
---------------------------------

This field accepts two new arguments:

``tag_options``
    A :ref:`TagOptions <tagoptions>` instance, containing
    :ref:`form options <form_options>` (model options will be ignored).

``autocomplete_tags``
    An iterable of tags to be embedded for autocomplete. This can either be
    a queryset of tag objects, or a list of tag objects or strings.

The ``clean`` method returns a single tag name string, or ``None`` if the
value is empty.


.. _form_tagfield:

``tagulous.forms.TagField``
---------------------------

This field accepts the same two new arguments as a ``SingleTagField``:

``tag_options``
    A :ref:`TagOptions <tagoptions>` instance, containing
    :ref:`form options <form_options>` (model options will be ignored).

``autocomplete_tags``
    An iterable of tags to be embedded for autocomplete. This can either be
    a queryset of tag objects, or a list of tag objects or strings.

The ``clean`` method returns a sorted list of unique tag names (a list of
strings) - or an empty list if there are no tags.



``tagulous.forms.TaggedInlineFormSet``
--------------------------------------

In most cases Tagulous works with Django's default inline model formsets, and
you don't need to do anything special.

However, there is a specific case where it doesn't: when you create an inline
formset for tagged models, with a tag as their parent model - eg when you edit
a tag and its corresponding instances of the tagged model. That is when you
must use the ``TaggedInlineFormSet`` class. For example::

    class Person(models.Model):
        name = models.CharField(max_length=255)
        title = tagulous.models.SingleTagField(initial='Mr, Mrs')

    PersonInline = forms.models.inlineformset_factory(
        Person.title.tag_model,
        Person,
        formset=tagulous.forms.TaggedInlineFormSet,
    )

This would allow you to generate a formset for all ``Person`` objects which
use a specific ``title`` tag.

Tagulous will automatically apply this fix in the admin site, as long as the
tag admin class is registered using ``tagulous.admin.register``.

Without the ``TaggedInlineFormSet`` class in this situation, the tag count will
be incorrect when adding tagged model instances, and editing will fail because
the default formset will try to use the tag name as a primary key.

The ``TaggedInlineFormSet`` class will only perform actions under this specific
relationship, so is safe to use in other situations.



.. _filter_autocomplete:

Filtering autocomplete tags
===========================

By default the tag field widget will autocomplete using all tags on the tag
model. However, you will often only want to use a subset of your tags - for
example, just the initial tags, or tags which the current user has used, or
tags which have been used in conjunction with another field on your model.

Because model tag fields are normal Django relationships, you can filter
embedded autocomplete tags by overriding the form's ``__init__`` method. To
filter an ajax autocomplete view, wrap ``tagulous.views.autocomplete`` in your
own view function which filters for you.

For examples of these approaches, see :ref:`example_filter_embedded` and
:ref:`example_filter_autocomplete_view`.


.. _autocomplete_adaptors:

Autocomplete Adaptors
=====================

Tagulous uses a javascript file it calls an ``adaptor`` to apply your chosen
autocomplete library to the Tagulous form field.

Only Select2 is included with Tagulous; if you want to use a different library,
you will need to add it to your project's static files, and add the relative
path under ``STATIC_URL`` to the appropriate ``TAGULOUS_`` settings.

Tagulous includes the following adaptors:

Select2 (version 4)
-------------------

The default adaptor, for `Select2 <https://select2.github.io/>`_.

Path:
    ``tagulous/adaptor/select2-4.js``

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

    Note that when used with inline formsets which raise the ``formset:added`` event
    (like in the Django admin site), Tagulous will automatically try to register tag
    fields in new formsets if ``defer=False``.

``width``
    This is the same as in Select2's documentation, but the Tagulous
    default is ``resolve`` instead of ``off``, for the best chance of
    working without complication.

All other settings will be passed to the Select2 constructor.



.. _custom_autocomplete_adaptor:

Writing a custom autocomplete adaptor
=====================================

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

    In addition to the dict from ``TagOptions`` containing the field's
    :ref:`form_options`, there will also be:

    ``required``
        A boolean indicating whether the form field is required or not

These settings can be used to initialise your autocomplete library of choice.
You should initialise it using ``data-tag-options``'s ``autocomplete_settings``
for default values.

For consistency with Tagulous's :ref:`python parser <python_parser>`, try to
replace your autocomplete library's parser with Tagulous's
:ref:`javascript parser <javascript_parser>`.

If you write an adaptor which you think would make a good addition to this
project, please do send it in or make a pull request on github - see
:doc:`contributing` for more information.

