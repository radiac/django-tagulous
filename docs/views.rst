===================
Views and Templates
===================

.. _form_media:

Form templates
==============

To render Tagulous fields in forms outside the admin site, add ``{{ form.media }}`` to
your template to include the JavaScript and CSS resources; for example::

    {% block content %}
        {{ form.media }}
        {{ form }}
    {% endblock %}

For an example of adding the JavaScript and CSS separately, see the
`example project templates`__

__ https://github.com/radiac/django-tagulous/tree/develop/example/example/templates


.. _autocomplete_views:

Autocomplete views
==================

Although Tagulous doesn't need any views by default, it does provide generic
views in :source:`tagulous/views.py` to support AJAX autocomplete requests.

``response = autocomplete(request, tag_model)``
    This takes the request object from the dispatcher, and a reference to the
    tag model which this is autocompleting.

    You can also pass in a QuerySet of the tag model, instead of the tag model
    itself, in order to filter the tags which will be returned.

    It returns an ``HttpResponse`` with content type ``application/json``. The
    response content is a JSON-encoded object with one key, ``results``, which
    is a list of tags.


``response = autocomplete_login(request, tag_model)``
    Same as ``autocomplete``, except is decorated with Django auth's
    ``login_required``.

These views look for two GET parameters:

``q``
    A query string to filter results by - used to match against the start of
    the string.

    Note: if using a sqlite database, matches on a case sensitive tag model
    may not be case sensitive - see the
    :ref:`option_case_sensitive` option for more details.

``p``
    The page number to return, if :ref:`option_autocomplete_limit` is set on
    the tag model.

    Default: ``1``

For an example, see the :ref:`example_autocomplete_views` example.


.. _tag_clouds:

Tag clouds
==========

Tag clouds are a common way to display tags. Rather than have a template tag
with templates and options for every eventuality, Tagulous simply offers a
:ref:`weight() <queryset_weight>` method on tag querysets, which adds a
``weight`` annotation to tag objects::

    # myapp/view.py
    def tag_cloud(request):
        ...
        tags = MyModel.tags.tag_model.objects.weight()
        ...

The ``weight`` value will be a number between ``TAGULOUS_WEIGHT_MIN`` and
``TAGULOUS_WEIGHT_MAX`` (see :ref:`settings`), although these can be overridden
by passing arguments to ``weight()`` for new min and/or max values, eg::

    tags = TagModel.objects.weight(min=2, max=4)

You can then render the tag cloud in your template as any other queryset, with
complete control over how they are displayed::

    {% if tags %}
        <h2>Tags</h2>
        <p>
        {% for tag in tags %}
            <a href="{{ tag.get_absolute_url }}" class="tag_{{ tag.weight }}">
                {{ tag.name }}
            </a>
        {% endfor %}
    {% endif %}

In that example, you would then define CSS classes for ``tag_1`` to ``tag_6``,
which set the appropriate font styles.

If you wanted to insert the tag cloud on every page, it would be easy to wrap
up in a custom template tag::

    # myapp/templatetags/myapp_tagcloud.py
    from django import template
    from myapp import models

    register = template.Library()
    @register.inclusion_tag('myapp/include/tagcloud.html')
    def show_results(poll):
        tags = models.MyModel.tags.tag_model.objects.weight()
        return {'tags': tags}

    # myapp/templates/tagcloud.html - see template example above
