.. _admin:

Admin
=====

Tag fields in ModelAdmin
------------------------

To support TagField and SingleTagField fields in the admin, you need to
register the Model and ModelAdmin using Tagulous's `register()` function,
instead of the standard one::

    class MyAdmin(admin.ModelAdmin):
        list_display = ['name', 'tags']
    tagulous.admin.register(MyModel, MyAdmin)

This will make a few changes to ``MyAdmin`` to add tag field support (detailed
below), and then register it with the default admin site using the standard
``site.register()`` call.

Alternatively you can specify a custom admin site by calling Tagulous's own
``register_site()``:

    # These two lines are equivalent:
    tagulous.admin.register(myModel, MyAdmin)
    tagulous.admin.register_site(admin.site, myModel, MyAdmin)

The changes Tagulous's ``register()`` function makes to the ``ModelAdmin`` are:

* Checks ``list_display`` for any tag fields, and adds functions to the
  ``ModelAdmin`` to display the tag string (unless an attribute with that name
  already exists)

Note:
* You can only provide the Tagulous ``register()`` function with one model.
* The admin class will be modified; bear that in mind if registering it more
  than once (ie with multiple admin sites).


Autocomplete settings
---------------------

The admin site can use different autocomplete settings to the public site by
changing the settings ``TAGULOUS_ADMIN_AUTOCOMPLETE_JS`` and
``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS``. You may want to do this to avoid jQuery
being loaded more than once, for example - assuming the version in Django's
admin site is compatible with the autocomplete library of your choice.

See `Settings`_ for more information


Managing the tag model
----------------------

You can also register a ModelAdmin to manipulate the tag table directly:

    class MyModelTagsAdmin(admin.ModelAdmin):
        list_display = ('name', 'count', 'protected')
        exclude = ('count',)
    admin.site.register(MyModel.tags.tag_model, MyModelTagsAdmin)

The example is for an auto-generated tag model, but it could equally be a
custom tag model.

However, if you do this you should set ``TAGULOUS_DISABLE_ADMIN_ADD = True`` to
disable the ``RelatedFieldWidgetWrapper`` in automatically generated admin
forms - see documentation for this setting for more details.

Remember that the relationship between your entries and tags are standard
``ForeignKey`` or ``ManyToMany`` relationships, so deletion propagation will
work as it would normally.

