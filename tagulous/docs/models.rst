.. _models:

Models
======

Tagulous offers two new model field types:
* ``TagField`` - conventional tags using a ``ManyToManyField`` relationship.
* ``SingleTagField`` - the same UI and helper functionality as a ``TagField``,
  but for a single tag using a ForeignKey relationship.

These will automatically create the models for the tags themselves, or you can
provide a custom model to use instead with ``to`` - see `Custom Models`_.


Model Field Arguments
---------------------

The ``SingleTagField`` supports most normal ``ForeignKey`` arguments, except
for ``to_field`` and ``rel_class``.

The ``TagField`` supports most normal ``ManyToManyField`` arguments, except
for ``db_table``, ``through`` and ``symmetrical``.

The following arguments can be passed to the field when adding it to the model:

``to``
    Manually specify a `Custom Tag Model`_, which must be a subclass of
    ``tagulous.models.TagModel``.
    
    If the tag model is specified, it should have a `TagMeta`_ class to ensure
    settings on different tag fields for the same model do not conflict.
    
    If the tag model has a TagMeta class, it will override all
    other arguments passed to the TagField constructor.
    
    Default: ``_Tagulous_<ModelName>_<FieldName>`` (auto-generated)
    
``protect_all``
    Whether all tags with count 0 should be protected from automatic deletion.
    
    If false, will be decided by ``tag.protected`` - see `Protected tags`_.
    
    Default: ``False``

``initial``
    List of initial tags for the tag model. Must be loaded into the database
    with the management command `initial_tags`_.
    
    Value can be a tag string to be parsed, or an array of strings with one
    tag in each string.
    
    If you find you need to update initial regularly, you would probably be
    better off using traditional fixtures with a `custom tag model`_
    
    Default: ``''``
    
``protect_initial``
    The ``protected`` state for any tags created by the `initial` argument -
    see `Protected tags`_.
    
    Default: True
    
``case_sensitive``
    If ``True``, tags will be case sensitive. For example, ``"django, Django"``
    would be two separate tags.
    
    If ``False``, tags will be capitalised according to the first time they are
    used.
    
    See also `force_lowercase`_
    
    Default: ``False``

:: _force_lowercase:
``force_lowercase``
    Force all tags to lower case
    
    Default: ``False``

``max_count``
    ``TagField`` only - this is not supported by ``SingleTagField``.
    
    Specifies the maximum number of tags allowed.
    
    Set to ``0`` to not have a limit to the maximum number of tags.
    
    If you are setting it to ``1``, consider using a `SingleTagField`_ instead.
    
    Default: ``0``
    
:: _autocomplete_view:
``autocomplete_view``
    Specify the view to use for autocomplete queries.
    
    This should be a value which can be passed to `reverse()`, eg the name of
    the view.
    
    If ``None``, all tags will be embedded into the form field HTML as the
    ``data-autocomplete`` attribute.
    
    If this is an invalid view, a ``ValueError`` will be raised.
    
    Default: ``None``
    
``autocomplete_limit``
    Maximum number of tags to provide at once, when ``autocomplete_view`` is
    set.
    
    If the autocomplete adaptor supports pages, this will be the number shown
    per page, otherwise any after this limit will not be returned.
    
    If ``0``, there will be no limit and all results will be returned

    Default: ``100``

``autocomplete_settings``
    Override the default ``TAGULOUS_AUTOCOMPLETE_SETTINGS``.
    
    Default: None

The ``related_name`` will default to ``<field>_set``, as is normal for
``ForeignKey``s and ``ManyToManyField``s. If using the same tag table on
multiple fields, it is highly recommended that you set this to something else
to avoid clashes.


:: _unbound_fields:

Unbound Fields
--------------

An unbound field (ie one called on the class attribute, eg ``MyModel.tags``)
will act in the same way an unbound field would for the underlying
``ForeignKey`` or ``ManyToManyField``, but has the following extra fields:
    
``tag_model``
    The related tag model

``tag_options``
    A `TagOptions`_ class, containing the options from the tag model's
    `TagMeta`_ and the arguments when initialising the field.


Bound Fields
------------

A bound field (called on an instance, eg ``instance.tags``) also acts in the
same way as a bound field would for the underlying ``ForeignKey`` or
``ManyToManyField`` by returning managers, but again these are supplemented
with extra functionality for managing tags.

A ``SingleTagField`` uses a `SingleTagManager`_, and a ``TagField`` uses a
``TagManager`_.


SingleTagManager
----------------

A bound ``SingleTagField`` uses this for its getter and setter methods.

``set``:
    Assigning a value to the bound field will call this method. It accepts a
    tag string, or an instance of the tag model.
    
    If it is passed ``None``, a current tag will be cleared if it is set.
    
    The instance must be saved afterwards.
    
    Example: ``person.title = "Mr"; person.save()``

``get``:
    Evaluating the bound field will call this method. It returns an instance
    of the tag model.
    
    Example: ``title_instance = person.title``


TagRelatedManager
-----------------

A bound ``TagField`` uses this for its setter method, and returns it when
evaluated; eg ``tag_manager = instance.tags``.

``set``:
    Assigning a value to the bound field will call this method. It accepts a
    `tag string <#Tag Strings>`_, or an iterable of strings or tag instances,
    eg a list of strings, or a queryset of Tag instances.
    
    If it is passed ``None``, any current tags will be cleared.
    
    The instance must be saved afterwards.
    
    Example: ``person.skills = 'Judo, "Kung Fu"'; person.save()``

``set_tag_string``
    Sets the tags for this instance, given a `tag string <#Tag Strings>`_.
    
    Example: ``person.skills.set_tag_string('Judo, "Kung Fu"'); person.save()``

``set_tag_list``
    Sets the tags for this instance, given an iterable of strings or tag
    instances.
    
    Example: ``person.skills.set_tag_list(['Judo', kung_fu_tag]); person.save()``

``get_tag_string``
    Gets the tags as a string
    
    Example: ``print person.skills.get_tag_string()``

``get_tag_list``
    Returns a list of strings for each tag
    
    Example: ``[print skill for skill in person.skills.get_tag_list()]``

``__unicode__``
    Same as ``get_tag_string``
    
    Example: ``print u'%s' % person.skills


A bound ``TagField`` can also be compared to other bound fields or tag strings
(order does not matter, and case sensitivity depends on tag field options)::

    if first.tags == second.tags:
        ...
    if first.tags != 'foo bar':
        ...


Tag Strings
-----------

A tag string is a string in tag format. This is parsed by an internal parser
which can be configured.


Protected tags
--------------

The tag model keeps a count of how many times each tag is referenced. When the
tag count reaches ``0``, the tag will be deleted unless its ``protected`` field
is ``True``, or the ``protect_all`` option has been used.

Note that this only happens when the count is updated, when the tag is added
or removed; tags can therefore be created directly on the model with the
default count of ``0`` to be assigned later.


Custom Tag Model
----------------

A custom tag model should extend ``tagulous.models.TagModel`` so that Tagulous
can find the fields and methods it expects.

A custom tag model is a normal model in every other way, except:

* It can have a `TagMeta`_ class to define default options for the class.
* If it uses a custom manager or queryset, check compatibility with the
  Tagulous `enhanced queryset`_ - but it'll probably be fine.

There is `an example <_example_custom_tag_model>`_ which illustrates both of
these.


TagMeta
~~~~~~~

The ``TagMeta`` class is a container for tag options, to be used when creating
a custom tag model.

Set any options listed in `Model Field Arguments`_ as class properties, except
for ``to``.

These options will be used as defaults when creating ``SingleTagField``s and
``TagField``s which set ``to`` to the custom class, but can be overridden by
arguments passed to the field.

``TagMeta`` can be inherited, so it can be set on abstract models. Options in
the ``TagMeta`` of a parent model can be overridden by options in the
``TagMeta`` of a child model.

Example
~~~~~~~




TagOptions
----------

The ``TagOptions`` class is a simple container for tag options. The options for
a model field are available from the ``tag_options`` property of the
`Unbound Field <_unbound_fields>`_.

All options listed in `Model Field Arguments`_ are available directly on the
object, except for ``to``. It also provides two instance methods:

``items(with_defaults=True)``
    Get a dict of all options
    
    If with_defaults is true, any missing settings will be taken from the
    defaults in ``constants.OPTION_DEFAULTS``.

``field_items(with_defaults=True)``
    Get a dict of just the options for a form field.
    
    If with_defaults is true, any missing settings will be taken from the
    defaults in ``constants.OPTION_DEFAULTS``.

Example::
    print MyModel.tags.tag_options.initial
    if "force_lowercase" in MyModel.tags.tag_options.items():
        ...

``TagOptions`` instances can be added together to create a new merged set of
options; note though that this is a shallow merge, ie the value of
``autocomplete_settings`` on the left will be replaced by the value on the
right::

    merged_options = TagOptions(
        autocomplete_settings={'width': 'resolve'}
    ) + TagOptions(
        autocomplete_settings={'allowClear': True}
    )
    # merged_options.autocomplete_settings == {'allowClear': True}

In the same way, setting ``autocomplete_settings`` on the field will replace
any default value.


Querying using tag fields
-------------------------

When querying a model which uses a tag field, remember that a
``SingleTagField`` is really a ``ForeignKey``, and a ``TagField`` is really a
``ManyToManyField``.

If you have not disabled the `enhanced queryset`_, you can compare a tag field
to a tag string in ``get``, ``filter`` and ``exclude``::

    qs = MyModel.objects.get(name="Bob", title="Mr", tags="red, blue, green")

Note that when referring to a ``TagField`` in this way, the filter will expect
an exact match - eg that it has all tags specified, but only those specified.
If you want to do partial matches, use standard many to many queries, eg::

    qs = MyModel.objects.get(tags__name__in=['red', 'blue', 'green'])


Database Migrations
-------------------

Tagulous supports South and Django 1.7 migrations.
