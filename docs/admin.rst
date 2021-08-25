=====
Admin
=====

Tag fields in ModelAdmin
========================

To support TagField and SingleTagField fields in the admin, you need to
register the Model and ModelAdmin using Tagulous's ``register()`` function,
instead of the standard one::

    import tagulous.admin
    class MyAdmin(admin.ModelAdmin):
        list_display = ['name', 'tags']
    tagulous.admin.register(MyModel, MyAdmin)

This will make a few changes to ``MyAdmin`` to add tag field support (detailed
below), and then register it with the default admin site using the standard
``site.register()`` call.

As with the normal registration call, the admin class is optional::

    tagulous.admin.register(myModel)

You can also pass a custom admin site into the `register()` function::

    # These two lines are equivalent:
    tagulous.admin.register(myModel, MyAdmin)
    tagulous.admin.register(myModel, MyAdmin, site=admin.site)

The changes Tagulous's ``register()`` function makes to the ``ModelAdmin`` are:

* Changes your ``ModelAdmin`` to subclass ``TaggedAdmin``
* Checks ``list_display`` for any tag fields, and adds functions to the
  ``ModelAdmin`` to display the tag string (unless an attribute with that name
  already exists)
* Switches an inline class to a ``TaggedInlineFormSet`` when necessary

Note:

* You can only provide the Tagulous ``register()`` function with one model.
* The admin class will be modified; bear that in mind if registering it with
  multiple admin sites. In that case, you may want to enhance the class
  manually, as described below.


Manually enhancing your ModelAdmin
==================================

The ``tagulous.admin.register`` function is the short way to enhance your admin
classes. If for some reason you can't use it (eg another library which has its
own ``register`` function, or you're registering it with more than one admin
site), you can do what it does manually:

1. Change your admin class to subclass ``tagulous.admin.TaggedModelAdmin``.

   This disables Django's green button to add a related field, which is
   incompatible with Tagulous.

2. Call ``tagulous.admin.enhance(model_class, admin_class)``.

   This finds the tag fields on the model class, and adds support for them to
   ``list_display``.

3. Register the admin class as normal

For example::

    import tagulous
    class MyAdmin(tagulous.admin.TaggedModelAdmin):
        list_display = ['name', 'tags']
    tagulous.admin.enhance(MyModel, MyAdmin)
    admin.site.register(MyModel, MyAdmin)


Autocomplete settings
=====================

The admin site can use different autocomplete settings to the public site by
changing the settings ``TAGULOUS_ADMIN_AUTOCOMPLETE_JS`` and
``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS``. You may want to do this to avoid jQuery
being loaded more than once, for example - assuming the version in Django's
admin site is compatible with the autocomplete library of your choice.

See :ref:`settings` for more information.

Because the select2 control defaults to use the same width as the form element it
replaces, you may find this a bit too small in some versions of the Django admin. You
could override this with :ref:`option_autocomplete_settings`, but that will change
non-admin controls too, so the best option would be to add a custom stylesheet to
``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS`` with a rule such as::

    .select2 {
        width: 75% !important;
    }


Managing the tag model
======================

Tagulous provides additional tag-related functionality for tag models, such as
the ability to merge tags. You can use Tagulous's ``register`` function to do
this for you - just pass it the tag field::

    tagulous.admin.register(MyModel.tags)

You can also specify the tag model directly::

    tagulous.admin.register(MyModel.tags.tag_model)
    tagulous.admin.register(MyCustomTagModel)

If you have a custom tag model and want to extend the admin class for extra
fields on your custom model, you can subclass the ``TagModelAdmin`` class to
get the extra tag management functionality::

    class MyModelTagsAdmin(tagulous.admin.TagModelAdmin):
        list_display = ['name', 'count', 'protected', 'my_extra_field']
    admin.site.register(MyCustomTagModel, MyModelTagsAdmin)

When overriding options, you should base them on the options in the default
``TagModelAdmin``::

    list_display = ['name', 'count', 'protected']
    list_filter = ['protected']
    exclude = ['count']
    actions = ['merge_tags']

The ``TagTreeModelAdmin`` also excludes the ``path`` field.

Remember that the relationship between your entries and tags are standard
``ForeignKey`` or ``ManyToMany`` relationships, so deletion propagation will
work as it would normally.

