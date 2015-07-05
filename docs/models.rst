.. _models:

Models
======

Tagulous offers two new model field types:

* ``TagField`` - conventional tags using a ``ManyToManyField`` relationship.
* ``SingleTagField`` - the same UI and helper functionality as a ``TagField``,
  but for a single tag using a ``ForeignKey`` relationship.

These will automatically create the models for the tags themselves, or you can
provide a custom model to use instead with ``to`` - see `Custom Models`_.

Tagulous is designed so that you can treat these as a ``CharField``, while still
leaving the underlying relationships available. For example, not only can you
assign a queryset or list of tag primary keys to a ``TagField``, but you can
also assign a list of strings (one per tag), or a tag string to parse.

Like a ``CharField``, changes made by assigning a value will not be committed
until the model is saved, although you can still make immediate changes by
calling the standard m2m methods ``add``, ``remove`` and ``clear``.

If ``TAGULOUS_ENHANCE_MODELS`` is ``True`` (which it is by default - see
`Settings`_) you can also ``get`` and ``filter`` by string, or pass tag field
values as strings into model constructors and ``object.create()`` as if it was
a ``CharField`` (see `Working with tagged models`_ for details of how that
works behind the scenes).


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
    
    Default: ``True``
    
``protect_all``
    Whether all tags with count 0 should be protected from automatic deletion.
    
    If false, will be decided by ``tag.protected`` - see `Protected tags`_.
    
    Default: ``False``

``case_sensitive``
    If ``True``, tags will be case sensitive. For example, ``"django, Django"``
    would be two separate tags.
    
    If ``False``, tags will be capitalised according to the first time they are
    used.
    
    See also `force_lowercase`_
    
    Default: ``False``

.. _force_lowercase:
``force_lowercase``
    Force all tags to lower case
    
    Default: ``False``

``max_count``
    ``TagField`` only - this is not supported by ``SingleTagField``.
    
    Specifies the maximum number of tags allowed.
    
    Set to ``0`` to not have a limit to the maximum number of tags.
    
    If you are setting it to ``1``, consider using a `SingleTagField`_ instead.
    
    Default: ``0``

``tree``
    If ``True``, slashes in tag names will be used to denote children, eg
    ``grandparent/parent/child``, and these relationships can be traversed.
    See `tag trees`_ for more details.
    
    If ``False``, slashes in tag names will have no significance, and no tree
    properties or methods will be present on tag objects.
    
    Default: ``False``

.. _autocomplete_view:
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

``get_absolute_url``
    A shortcut for defining a ``get_absolute_url`` method on the tag model.
    Only used when defined in tag fields which auto-generate models.
    
    It is common to need to get a URL for a tag, so rather than creating a
    custom ``TagModel`` just to implement a ``get_absolute_url`` method, you
    can pass this argument a callback function.
    
    The callback function will be passed the tag object, and should return the
    URL for the tag. See the `Tag URL`_ example for a simple lambda argument.
    
    If not set, the method ``get_absolute_url`` will not be available and an
    ``AttributeError`` will be raised.
    
    Default: None

``verbose_name_singular``, ``verbose_name_plural``
    When a tag model is auto-generated from a field, it is given a
    ``verbose_name`` based on the tagged model's name and the tag field's
    name; the ``verbose_name_plural`` is the same, but with an added ``s``
    at the end. This is primarily used in the admin.
    
    However, this will sometimes not make grammatical sense; these two
    arguments can be used to override the field name component of the model
    name.
    
    The ``verbose_name_singular`` will usually be used with a ``TagField`` -
    for example, the singular name for the auto-generated model for
    ``MyModel.tags`` will be ``My model tags``; this can be corrected by
    setting ``verbose_name_singular="tag"`` in the field definition.
    
    The ``verbose_name_plural`` will usually be used with a ``SingleTagField`` -
    for example, the plural name for the auto-generated model for
    ``MyModel.category`` will be ``My model categorys``; this can be corrected
    by setting ``verbose_name_plural="categories"`` in the field definition.
    
    If one or both of these are not set, Tagulous will try to find the field
    name from its ``verbose_name`` argument, falling back to the field name.
    
The ``related_name`` will default to ``<field>_set``, as is normal for
a ``ForeignKey`` or ``ManyToManyField``. If using the same tag table on
multiple fields, it is highly recommended that you set this to something else
to avoid clashes.


.. _unbound_fields:

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

``set``
    Assigning a value to the bound field will call this method. It accepts a
    tag string, or an instance of the tag model.
    
    If it is passed ``None``, a current tag will be cleared if it is set.
    
    The instance must be saved afterwards.
    
    Example: ``person.title = "Mr"; person.save()``

``get``
    Evaluating the bound field will call this method. It returns an instance
    of the tag model.
    
    Example: ``title_instance = person.title``


TagRelatedManager
-----------------

A bound ``TagField`` uses this for its setter method, and returns it when
evaluated; eg ``tag_manager = instance.tags``.

``set``
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

``reload()``
    Discard any unsaved changes to the tags and load tags from the database

``save(force=False)``
    Commit any tag changes to the database.
    
    If you are only changing the tags you can call this directly to reduce
    database operations.
    
    In most circumstances you can ignore the ``force`` flag:
    
    * The manager has a ``.changed`` flag which is set to ``False`` whenver the
      internal tag cache is loaded or saved. It is set to ``True`` when the
      tags are changed without being saved.
      
    * If ``force=False`` (default), this method will only update the database
      if the ``.changed`` flag is ``True`` - in other words, the database will
      only be updated if there are changes to the internal cache since last
      load or save.
      
    * If ``force=True``, the ``.changed`` flag will be ignored, and the current
      tag status will be forced upon the database. This can be useful in the
      rare cases where you have multiple references to the same database
      object, and want the tags on this instance to override any changes other
      instances may have made.
    
    You do not need to call this if you are saving the instance; any changes to
    tags will be saved as part of that process.
    
    Example: ``person.skills.save()``

``add(tag, tag, ...)``
    Based on a normal ``ManyToManyField``'s ``.add`` method; adds a list of
    tags or tag names directly to the instance - no need to save.
    
    Will call ``reload()`` first, so any unsaved changes to tags will be lost.
    
    Note, this does not parse tag strings - you will need to pass separate tags
    as either instances of the tag model, or as separate strings.
    
    Example: ``person.skills.add('Judo', kung_fu_tag)

``remove(tag, tag, ...)``
    Based on a normal ``ManyToManyField``'s ``.remove`` method; removes a list
    of tags or tag names directly from the instance - no need to save.
    
    Will call ``reload()`` first, so any unsaved changes to tags will be lost.
    
    Note, this does not parse tag strings - you will need to pass separate tags
    as either instances of the tag model, or as separate strings.
    
    Example: ``person.skills.remove('Judo', kung_fu_tag)

``clear()``
    Based on a normal ``ManyToManyField``'s ``.clear`` method; clears all tags
    from the instance immediately - no need to save.
    
    Example: ``person.skills.clear()``


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


Tag Models
----------

Tag models subclass ``tagulous.models.TagModel``, and have the following
fields:

``name``
    A ``CharField`` containing the name (string value) of the tag.
    
    Must be unique.

``slug``
    A unique ``SlugField``, generated automatically from the name when first
    saved.

``count``
    An ``IntegerField`` holding the number of times this tag is in use.

``protected``
    A ``BooleanField`` indicating whether this tag should be protected from
    deletion when the count reaches 0.

It also has several methods primarily for internal use, but some may be useful:

``get_related_objects()``
    Return a list of instances of other models which refer to this tag; see
    the API for more details

``update_count()``
    In case you're doing something weird which causes the count to get out
    of sync, call this to update the count, and delete the tag if appropriate.

``merge_tags(tags)``
    Merge the specified tags into this tag.
    
Its standard manager and queryset also supports the following:

``filter_or_initial(...)``
    Calls the normal ``filter(...)`` method, but then adds on any initial tags
    which may be missing.


Custom Tag Models
-----------------

A custom tag model should subclass ``tagulous.models.TagModel``, so that
Tagulous can find the fields and methods it expects, and so it uses the
appropriate tag model manager and queryset.

A custom tag model is a normal model in every other way, except it can have a
`TagMeta`_ class to define default options for the class.

There is `an example <_example_custom_tag_model>`_ which illustrates how to
create a custom tag model.

If you want to use tag trees, you will need to subclass
``tagulous.models.TagTreeModel`` instead. The only difference is that
there will be extra fields on the model - see `tag trees`_ for more details.


TagMeta
~~~~~~~

The ``TagMeta`` class is a container for tag options, to be used when creating
a custom tag model.

Set any options listed in `Model Field Arguments`_ as class properties, except
for ``to``.

These options will be used as defaults when creating a ``SingleTagField`` or
``TagField`` which set ``to`` to the custom class, but can be overridden by
arguments passed to the field.

``TagMeta`` can be inherited, so it can be set on abstract models. Options in
the ``TagMeta`` of a parent model can be overridden by options in the
``TagMeta`` of a child model.



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
``ManyToManyField``. You can always query using these relationships.

In addition you can compare a tag field to a tag string in ``get``, ``filter``
and ``exclude``::

    qs = MyModel.objects.get(name="Bob", title="Mr", tags="red, blue, green")

(This requires the setting ``TAGULOUS_ENHANCE_MODELS`` to be ``True``, or for
you to use the subclasses detailed in `Working with tagged models`_.)

Note that when referring to a ``TagField`` in this way, the filter will expect
an exact match - eg that it has all tags specified, but only those specified.
If you want to do partial matches, use standard many to many queries, eg::

    qs = MyModel.objects.get(tags__name__in=['red', 'blue', 'green'])


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


Tag Trees
---------

Tags in tag trees denote parents using a forward slash, ``/``; for example,
``Animal/Mammal/Cat`` is a ``Cat`` with a parent of ``Mammal`` and grandparent
of ``Animal``.

To use a slash in a tag name, escape it with a second slash; for example
``Animal/Mammal/Cat//Kitten`` is a ``Cat/Kitten``.

Tag trees use the ``TagTreeModel`` - a subclass of ``TagModel``. This means
that in addition to the normal tag model, there are additional fields and
properties available:

``parent``
    The parent tag. Tagulous sets this automatically when saving, creating
    missing ancestors as needed.

``children``
    The reverse relation manager for ``parent``, eg ``mytag.children.all()``.

``label``
    The name of the tag without its ancestors.
    
    Example: a tag named ``Animal/Mammal/Cat`` has the label ``Cat``

``slug``
    The slug for the tag label.
    
    Example: a tag named ``Animal/Mammal/Cat`` has the slug ``cat``

``path``
    The path for this tag - this slug, plus all ancestor slugs, separated by
    the ``/`` character, suitable for use in URLs. Tagulous sets this
    automatically when saving.

    Example: a tag named ``Animal/Mammal/Cat`` has the path
    ``animal/mammal/cat``

``level``
    The level of this tag in the tree (starting from 1).

``get_ancestors()``
    Returns a queryset of all ancestors, ordered by level.

``get_descendants()``
    Returns a queryset of all descendants, ordered by level.

Because tree tag names are fully qualified (include all ancestors) and unique,
there is no difference to normal tags in how they are set or compared.


Converting from to tree tags from normal tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using South
+++++++++++

These instructions will convert an existing ``TagModel`` to a ``TagTreeModel``.
Look through the code snippets and change :

1. Create a data migration to escape the tag names; for example::

    def forwards(self, orm):
        for tag in orm['myapp._Tagulous_MyModel_tags'].objects.all():
            tag.name = tag.name.replace('/', '//')
    
   You can skip this step if you have been using slashes in normal tags and
   want them to be converted to nested tree nodes.

2. Create a schema migration to change the model fields. Because paths are not
   allowed to be null, South will prompt you for a value; answer with ``x``.
   
   However, because paths are also unique, the default migration will cause
   integrity errors. Tagulous includes a helper function to get around this -
   change your schema migration to use it::

    def forwards(self, orm):
        from tagulous.models.migrations import add_unique_column
        
        # Adding field '_Tagulous_MyModel_tags.path'
        add_unique_column(
            self, db, orm['myapp._Tagulous_MyModel_tags'], 'path',
            lambda obj: setattr(obj, 'path', str(obj.pk)),
            'django.db.models.fields.TextField',
        )
    
    This will temporarily set the ``path`` of each tag to the tag's pk.
    
3. Run the migrations

4. From a python shell, rebuild the tree to set paths::
   
    from myapp import models
    models._Tagulous_MyModel_tags.objects.rebuild()
   
   If you skipped step 1, this will also create and set parent tags as
   necessary.
   
   It is best practice to do this manually after running the migrations, in
   case you change your code in the future and the migration can no longer
   access ``myapp.models._Tagulous_MyModel_tags``. If you are confident this
   will not be a problem, you could do this in a second data migration.


Working with tagged models
--------------------------

Models which have tag fields are called tagged models (not to be confused with
tag models, which are the models which store the tags - in the
`Automatic Models`_ example ``Person`` is the tagged model). In most
situations, all you need to do is add the tag field to the model and Tagulous
will do the rest.

Because Tagulous's fields work by subclassing ``ForeignKey`` and
``ManyToManyField``, there are some places in Django's models where you would
expect to use tag strings but cannot - constructors and filtering, for example.
Tagulous therefore provides base classes to add this functionality to Django's
core.

If ``TAGULOUS_ENHANCE_MODELS`` is ``True`` (which it is by default - see
`Settings`_), these base classes will be applied automatically. Tagulous does
this by listening for the ``class_prepared`` signal, sent when a model has been
constructed; if it contains tag fields, Tagulous will add ``TaggedModel`` to
the base classes of the model, and add ``TaggedManager`` to the managers' base
classes - which in turn will add ``TaggedQuerySet`` to the querysets created by
the managers. This will all happen seamlessly behind the scenes; the only thing
you may notice is that the names of your manager and queryset classes now have
the prefix ``CastTagged`` to indicate that they have been automatically cast to
their equivalents for tagged models.

However, if you want to avoid this automatic subclassing, you can set
``TAGULOUS_ENHANCE_MODELS`` to ``False`` and manage this yourself:

``tagulous.models.TaggedModel``
    The subclass for tagged models. Changes the model constructor so that
    TagField values can be passed as keywords.

``tagulous.models.TaggedManager``
    The subclass for managers of tagged models. Only exists to ensure querysets
    are subclasses of ``tagulous.TaggedQuerySet``.
    
``tagulous.models.TaggedQuerySet``
    The subclass for querysets on tagged models. Changes filter and exclude to
    work with string values, and create and get_or_create to work with string
    values and ``TagField``s.

These classes each have a class method ``cast_class`` which can change existing
classes so that they become ``CastTagged`` subclasses of themselves; for
example::

    class MyModel(tagulous.TaggedModel):
        name = models.CharField(max_length=255)
        tags = tagulous.models.TagField()
        objects = tagulous.models.TaggedManager.cast_class(MyModelManager)
        other_manager = MyOtherManager
    tagulous.models.TaggedManager.cast_class(MyModel.other_manager)

This can be useful when working with other third-party libraries which insist
on you doing things a certain way.


Database Migrations
-------------------

Tagulous supports South and Django 1.7 migrations.


