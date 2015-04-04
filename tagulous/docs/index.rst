===============================
Django Tagulous - Fabulous Tags
===============================

A tagging library for Django built on ForeignKey and ManyToManyField, giving
you all their normal power with a sprinkling of tagging syntactic sugar.


Contents
========

.. toctree::
 :maxdepth: 2

 installation
 usage
 models
 forms
 views
 admin


Comparison with other tagging libraries
=======================================

Tagulous takes a different approach to other tagging libraries for Django by
directly extending ``ForeignKey`` and ``ManyToManyField``, with the option to
automatically create separate tag models without using generic relations. This
means it has a simpler syntax, and has more flexibility and reliability when
managing and querying tags.

It also aims to be a self-contained package by including all commonly-required
tagging functionality, such as autocomplete and template tags.


Separate tag models, no generic relations
-----------------------------------------

The original tagging library for Django was the now-defunct
`django-tagging <https://github.com/brosner/django-tagging>`_, which has been
replaced by the fork
`django-tagging-ng <https://github.com/svetlyak40wt/django-tagging-ng>`_.
These use a registration approach to add a pseudo-field to the model
(as ``tags`` by default), which provides a simple interface for setting and
getting tags. It also adds a manager (default name ``tagged``) for retrieving
models based on tags. The popular
`django-taggit <https://github.com/alex/django-taggit>`_ is added to models
using a manager, which is essentially django-tagging's ``tags`` pseudo-field
and ``tagged`` manager in one.

In both libraries tags are stored in a single tag model, which means there can
only be one set of tags for the site - different models cannot use different
sets of tags, and a model can only ever have one tag field. In contrast,
Tagulous can automatically create the necessary models for each field, and lets
you explicity state which fields should share tags.

They also store the relationship between tags and tagged items using a
`GenericForeignKey`, but generic relations tend to be second-class citizens in
Django, often slower, lacking functionality and having more bugs compared to
standard ``ForeignKey`` and ``ManyToManyField`` relationships. Tagulous only
uses these standard relationships, so all database queries and aggregations
will function exactly as expected, without any limitations.

While django-taggit can be configured to operate in a similar way to Tagulous
with separate tag models, and ``through`` models using standard relationships,
it uses a more verbose syntax to do so, with these custom models having to be
explicitly created.


Tagulous does more
------------------

Traditional tags are ``ManyToManyFields``, but Tagulous also supports
``ForeignKey``s - a very similar API for managing many-to-one relationships
which users are allowed to add options to.

Unlike django-tagging-ng and django-taggit, Tagulous also has built-in support
for autocomplete in public and admin sites, by default using Select2 (although
this can be easily customised using `autocomplete adaptors`_).

Unlike django-tagging, Tagulous also comes with autocomplete for public and
admin sites, and has template tags without needing a third-party plugin like
django-taggit.

Tagulous also has a more robust tag string parser, which is also implemented in
javascript for full compatibility with client-side autocompletion.
