=====
Admin
=====

Tag fields in ModelAdmin
========================

Tagulous automatically enhances Django's admin so that tag fields work correctly
when you register models using the standard Django admin API::

    from django.contrib import admin
    from myapp.models import MyModel

    @admin.site.register(MyModel)
    class MyAdmin(admin.ModelAdmin):
        list_display = ['name', 'tags']


Displaying tags as links
========================

By default, tag fields in ``list_display`` are rendered as plain text. To render
each tag as a link to its admin change view, use ``list_display_tag_links``::

    from tagulous.admin import list_display_tag_links

    class MyAdmin(admin.ModelAdmin):
        list_display = ['name', 'tags_links']
        tags_links = list_display_tag_links('tags')

    admin.site.register(MyModel, MyAdmin)

This works for both ``TagField`` and ``SingleTagField``. If the tag model is not
registered with the admin site, tags are shown as plain text instead.


Autocomplete settings
=====================

The admin site can use different autocomplete settings to the public site by
changing the settings ``TAGULOUS_ADMIN_AUTOCOMPLETE_JS`` and
``TAGULOUS_ADMIN_AUTOCOMPLETE_CSS``. You may want to do this to change the autocomplete
library.

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
the ability to merge tags. Auto-enhancement applies this automatically when you
register a tag model with the standard admin::

    admin.site.register(MyModel.tags.tag_model)

You can also pass the tag field descriptor or the tag model class directly::

    admin.site.register(MyModel.tags.tag_model)
    admin.site.register(MyCustomTagModel)

If you have a custom tag model, subclass ``TagModelAdmin``::

    from tagulous.admin import TagModelAdmin

    class MyModelTagsAdmin(TagModelAdmin):
        list_display = ['name', 'count', 'protected', 'my_extra_field']

    admin.site.register(MyCustomTagModel, MyModelTagsAdmin)

When overriding options, you should base them on the defaults in
``TagModelAdmin``::

    list_display = ['name', 'count', 'protected']
    list_filter = ['protected']
    exclude = ['count']
    actions = ['merge_tags']

The ``TagTreeModelAdmin`` also excludes the ``path`` field.

Remember that the relationship between your entries and tags are standard
``ForeignKey`` or ``ManyToMany`` relationships, so deletion propagation will
work as it would normally.


Disabling auto-enhancement
===========================

You can set ``TAGULOUS_ENHANCE = False`` in your settings to opt out of the
global ``AdminSite.register`` patch. You can then apply tag field support
selectively by subclassing ``TaggedModelAdmin`` directly::

    from tagulous.admin import TaggedModelAdmin

    @admin.site.register(MyModel)
    class MyAdmin(TaggedModelAdmin):
        list_display = ['name', 'tags']

