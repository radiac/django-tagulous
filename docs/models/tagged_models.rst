=============
Tagged Models
=============

Models which have tag fields are called tagged models. In most situations, all
you need to do is add the tag field to the model and Tagulous will do the rest.

Because Tagulous's fields work by subclassing ``ForeignKey`` and
``ManyToManyField``, there are some places in Django's models where you would
expect to use tag strings but cannot - constructors and filtering, for example.
Tagulous therefore adds this functionality through the :ref:`taggedmodel` base class for tagged models.

If ``TAGULOUS_ENHANCE_MODELS = True`` (which it is by default - see
:ref:`settings`), this base class will be applied automatically, otherwise read
on to :ref:`taggedmanually`.

.. note::

    Tagulous sets ``TaggedModel`` as the base class for your existing tagged
    model by listening for the ``class_prepared`` signal, sent when a model has
    been constructed. If the model contains tag fields, Tagulous will
    dynamically add ``TaggedModel`` to the model's base classes and
    ``TaggedManager`` to the manager's base classes, which in turn adds
    ``TaggedQuerySet`` to the querysets the manager creates. It does this by
    calling the ``cast_class`` class method on each of the base classes, which change the original classes in place.

    This all happens seamlessly behind the scenes; the only thing you may
    notice is that the names of your manager and queryset classes now have the
    prefix ``CastTagged`` to indicate that they have been automatically cast to
    their equivalents for tagged models.


Tagged model classes
====================

.. _taggedmodel:

``tagulous.models.TaggedModel``
-------------------------------

This is the base class for all tagged models. It changes the model constructor
so that ``TagField`` values can be passed as keywords.


.. _taggedmanager:

``tagulous.models.TaggedManager``
---------------------------------

The base class for managers of tagged models. It only exists to ensure querysets
are subclasses of ``tagulous.TaggedQuerySet``.


.. _taggedqueryset:

``tagulous.models.TaggedQuerySet``
----------------------------------

The base class for querysets on tagged models. It changes ``get``, ``filter`` and
``exclude`` to work with string values, and ``create`` and ``get_or_create`` to
work with string and ``TagField`` values.

It also adds ``get_similar_objects()`` - see :ref:`finding_similar_objects` for usage.

See :ref:`querying` for more details.


.. _taggedmanually:

Setting tagged base classes manually
====================================

However, if you want to avoid this automatic subclassing, you can set
``TAGULOUS_ENHANCE_MODELS = False`` and manage this yourself:

The three tagged base classes each have a class method ``cast_class`` which can
change existing classes so that they become ``CastTagged`` subclasses of
themselves; for example::

    class MyModel(tagulous.TaggedModel):
        name = models.CharField(max_length=255)
        tags = tagulous.models.TagField()
        objects = tagulous.models.TaggedManager.cast_class(MyModelManager)
        other_manager = MyOtherManager
    tagulous.models.TaggedManager.cast_class(MyModel.other_manager)

This can be useful when working with other third-party libraries which insist
on you doing things a certain way.


.. _querying:

Querying using tag fields
=========================

When querying a tagged model, remember that a ``SingleTagField`` is really a
``ForeignKey``, and a ``TagField`` is really a ``ManyToManyField``. You can
query using these relationships in conventional ways.

If you have correctly made your tagged model subclass :ref:`taggedmodel`, you
can also compare a tag field to a tag string in ``get``, ``filter`` and
``exclude``::

    qs = MyModel.objects.get(name="Bob", title="Mr", tags="red, blue, green")

When querying a tag field, case sensitivity will default to whatever the tag
field option was. For example, if the ``title`` tag field above was defined
with ``case_sensitive=False``, ``.filter(title='Mr')`` will match ``Mr``,
``mr`` etc.

Note that when querying a ``TagField`` in this way, the returned queryset will
include (or exclude) any object which contains all the specified tags - but it
may also have other tags. To only return objects which have the specified tags
and no others, use the ``__exact`` field lookup suffix::

    # Find all MyModel objects which have the tag 'red':
    qs = MyModel.objects.filter(tags='red')
    # (will include those tagged 'red, blue' etc)

    # Find all MyModel objects which are only tagged 'red':
    qs = MyModel.objects.filter(tags__exact='red')
    # (will not include those tagged 'red, blue')

This currently does not work across database relations; you will need to use
the ``name`` field on the tag model for those::

    # Find
    qs = MyRelatedModel.objects.filter(
        foreign_model__tags__name__in=['red', 'blue', 'green'],
    )


.. _filter_by_related:

Filtering tags by related model fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because tag fields use standard database relationships, you can easily filter
the tags by other fields in your model.

For example, if your model ``Record`` has a ``tags`` TagField and an ``owner``
foreign key to ``auth.User``, to get a list of tags which that user has used::

    myobj.tags.tag_model.objects.filter(record__owner=user)

There is a ``filter_or_initial`` helper method on a ``TagModel``'s manager and
queryset, which will add initial tags to your filtered queryset::

    myobj.tags.tag_model.objects.filter_or_initial(record__owner=user)


.. _finding_similar_objects:

Finding similar objects
~~~~~~~~~~~~~~~~~~~~~~~

The QuerySet on a tagged model provides the method ``get_similar_objects``, which takes
the instance and field name to compare similarity by, and returns a queryset of similar
objects from that tagged model, ordered by similarity::

    myobj = MyModel.objects.first()
    similar = MyModel.objects.get_similar_objects(myobj, 'tags')

There is a convenience wrapper on the related manager which detects the instance and
field to compare by::

    similar = myobj.tags.get_similar_objects()

Although less useful, there is a similar function for single tag fields, which finds all
objects with the same tag::

    similar = myobj.singletag.get_similar_objects()

The similar querysets will exclude the object being compared - in the above examples,
``myobj`` will not be in the queryset.
