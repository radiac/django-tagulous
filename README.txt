===============================
Django Tagulous - Fabulous Tags
===============================

A tagging library for Django built on ForeignKey and ManyToManyField, giving
you all their normal power with a sprinkling of tagging syntactic sugar.

Features
========

* Easy to install - simple requirements, just drops into your site
* Autocomplete support out of the box - uses Select2, also supports chosen,
  selectize and jQuery UI
* Ability to have tag sets local to a field, or shared between them
* Multiple independent tag fields on a single model
* All the other features you'd expect a tagging library to have

See `Example Usage`_ to see how it works in practice.

Version 0.4.5

* See `CHANGES <CHANGES>`_ for full changelog and roadmap
* See `UPGRADE <UPGRADE.rst>`_ for how to upgrade from earlier releases




Notes
=====

Testing:
    ./manage.py test tagulous

Remember, because TagField is a M2M field, you can't read or write to it until
the instance has been saved.

Because SingleTagField is a ForeignKey, it may return None rather than a
TagModel instance - so if you want to get the model from an instance, you
should not rely on the .model property without checking it is not None first.

When you set a TagField, the changes will be saved in the database immediately
as they would be normally for a ManyToManyField.

When you set a SingleTagField, you need to save the model instance as is normal
for a ForeignKey.

Because the tag count reflects the status of the database, changes to a
SingleTagField will not update the count until the model containing the field
is saved (or deleted).

A SingleTagField needs to keep track of its status; it will do this in a new
attribute on each model instance, named _FIELD_tagulous, where FIELD is the
name of the field. In other words:

class MyModel(models.Model):
    singletag = SingleTagField()
    # Also creates:
    # singletag_id          The ID of the Tag object
    # _singletag_tagulous   The tag field's internal status (the manager)
    # _singletag_cache      Django's internal cache

The SingleTagField does lie a little bit if changes haven't been saved. If you
set the tag on a SingleTagField, it will store the tag name, then either load
the Tag object, or if it doesn't exist it will dynamically create one when
you request it again. This is because the Tag model tags in the database, and
their counts, must always reflect the values in the database. The count will
only be updated once the model instance has been saved.

Django caches its ForeignKey lookups, so if you want to do anything with a Tag
object (use the Tag count for example), make sure the instance is loaded fresh.
This does not apply to save and delete operations - they are side effects, so
they will flush the cache to ensure count changes are accurate.

A SingleTagField with blank=True must also have null=True.

If your tests require a tag field to have been loaded with initial tags, you
must call tagulous.models.initial.model_initialise_tags(myModel) from your setUp().

You can compare a tag field against a string - the string will be parsed into
tags, and matched according to the tag options for that field.
