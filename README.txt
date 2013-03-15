Tagulous
========

Fabulous tags


Overview
--------

Tagulous provides convenient syntax and functions for associating one or more
tags with a model. It supports:
* Multiple tag fields on a single model
* Autocomplete
* Ability to have tag sets local to a field, or shared between them

It offers two new model field types:
* TagField - conventional tags using a ManyToMany relationship
* SingleTagField - the same UI for a single tag using a ForeignKey relationship



Example usage:

    from django.db import models
    import tagulous
    
    class Person(models.Model):
        title = tagulous.SingleTagField(initial="Mr, Mrs, Miss, Ms")
        name = models.CharField(max_length=255)
        tags = tagulous.TagField()
    
This will create two new models:
    _Tagulous_Person_title      Tags for the title field
    _Tagulous_Person_tags       Tags for the tags field

Person.title will now act as a ForeignKey to _Tagulous_Person_title
Person.tags will now act as a ManyToManyField to _Tagulous_Person_tags

There are minor differences between the two; for example, they allow you to
specify a string when setting the value, and they have a `model` property
so that you can get at the tag model for that field. However, they are based
on ForeignKey and ManyToManyField, so you can do everything with them that
you would normally do.

To set tags:

    instance = MyModel()
    instance.save()
    instance.tags.set_tags('foo bar')

Manual tag class:

    import tagulous
    class MyTags(tagulous.TagModel):
        class TagMeta:
            # Options as passed to TagField
    
    class MyModel(models.Model):
        ...
        tags = tagulous.TagField(tag_model=MyTags)

Testing:
    ./manage.py test tagulous


Forms
-----

Because this is based on a ManyToManyField, if you call `.save(commit=False)`
(eg your form consists of formsets), remember to call `.m2m_save()` after
to save the tags.

If you have a straight form, `.m2m_save()` will be called automatically so you
don't need to do anything else.

The JavaScript code requires jQuery 1.4.3 or later. For convenience there is a
bundled copy of jQuery 1.7.2 in the tagulous static directory. This is not
included in public pages by default, but can be configured by changing the
TAGULOUS_PUBLIC_JQUERY setting.


Admin
-----

To add support TagField and SingleTagField fields in the admin, you need to
register the Model and ModelAdmin using Tagulous's `register()` function,
instead of the standard one, `django.contrib.admin.site.register()`:

    class MyAdmin(admin.ModelAdmin):
        list_display = ['name', 'tags']
    tagulous.admin.register(myModel, MyAdmin)

This will make a few changes to MyAdmin to add tag field support (detailed
below), and then call the standard admin `site.register()` to register as
normal.

Alternatively you can specify a custom admin site by calling `register_site()`:

    # These two lines are equivalent:
    tagulous.admin.register(myModel, MyAdmin)
    tagulous.admin.register_site(admin.site, myModel, MyAdmin)

The changes tagulous's `register()` function makes to the ModelAdmin are:

* Checks list_display for any tag fields, and adds functions to the ModelAdmin
  to display the tag string (unless an attribute with that name already exists)

Note:
* You can only provide the Tagulous `register()` function with one model.
* The admin class will be modified, so you must be careful if registering it
  more than once.

The JavaScript code requires jQuery 1.4.3 or later, but the admin site of both
Django 1.3 and 1.4 only uses jQuery 1.4.2. There is therefore a bundled copy of 
jQuery 1.7.2 in the tagulous static directory. This is included by default, but
can be configured by changing the TAGULOUS_ADMIN_JQUERY setting, in case you
already have a more recent version of jQuery in your admin site.


Notes
-----

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
attribute on each model instance, named FIELD_tagulous, where FIELD is the
name of the field. In other words:

class MyModel(models.Model):
    singletag = SingleTagField()
    # Also creates:
    # singletag_id          The ID of the Tag object
    # _singletag_tagulous   The tag field's internal status
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
must call tagulous.models.model_initialise_tags(myModel) from your setUp().

You can compare a tag field against a string - the string will be parsed into
tags, and matched according to the tag options for that field.



To Do
-----

Add a way to allow tags to be set before the item is saved

Known bugs:
* get_or_create(singletag='Bob') will fail due to get() part

Add support for comparing tag fields against lists of tags
Test comparing one model tag field against another
Test single tag manager
Test (and add support for, if necessary), BaseTagManager.__contains__

Support filtering tags against another field in the model, eg by user

Test forms
Make sure all tag options are tested - autocomplete_limit is not

Look into replacing widget with jquery.ui autocomplete
Add settings.Tagulous_Autocomplete_Installed to use a tagwidget.js that expects my autocomplete class available on the page.

Test
    Order of fields - new model with two M2M fields either side, check
    model._meta.local_many_to_many
    max_count
    stuff going through to forms:
        test that django hasnt changed
        that widget gets tag_options and autocomplete

Widget
    Nice tag entry


Roadmap
-------

Template tags
    {% tagcloud obj.tags %}, using the block contents as a template for each entry
    {% taglinks obj.tags %}, using the block contents as a template for each link

Support for heirarchical tags
    Add to tag.Tag.__init__ kwargs:
        tag_child_separator='.'
        tag_add_to_parent=False
    "foo.bar" creates tag 'foo' and child tag 'bar'
    Will put it in 'bar'
    Will also add to 'foo' (and all other parents) if tag_add_to_parent=True
    ?? Or better to just put it in 'bar', then provide queryset to get all objects in child tags?

Advanced admin features
    Ability to merge tags
    Ability to change tag hierarchy

Migration support (if possible)
    To and from django-tagging
    To and from django-taggit


FAQ
----

Autocomplete
    It uses jquery - why not jquery ui?
        Future plans require a custom dropdown, and an autocomplete isn't hard,
        so using a custom autocomplete widget from initial release makes sense.
    I use other autocomplete widgets elsewhere - how can I make them look the same?
        The autocomplete code which Tagulous uses has been released as a
        stand-alone jquery plugin, so you have two options: either re-style the
        tagulous widget, or switch to use the same autocomplete as tagulous.
        // ++ Release the jquery plugin
        // ++ Styling
        // ++ Using the same autocomplete
        
        
    