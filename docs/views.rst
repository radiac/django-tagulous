.. _views:

Views
=====

Although Tagulous doesn't need any views by default, it does provide generic
views in ``views.py`` to support AJAX autocomplete requests.

``response = autocomplete(request, tag_model)``
    This takes the request object from the dispatcher, and a reference to the
    tag model which this is autocompleting.
    
    You can also pass in a QuerySet of the tag model, instead of the tag model
    itself, in order to filter the tags which will be returned.
    
    It returns an ``HttpResponse`` with mimetype ``application/json``. The
    response content is a JSON-encoded object with one key, ``results``, which
    is a list of tags.
    
    
``response = autocomplete_login(request, tag_model)``
    Same as ``autocomplete``, except is decorated with Django auth's
    ``login_required``.

For an example, see `Autocomplete Views`_.


Tag clouds
----------

Tag clouds are a common way to display tags. Rather than have a template tag
with templates and options for every eventuality, Tagulous simply offers a
``weight(..)`` method on tag querysets (see
`queryset documentation <_queryset_weight>`_), which adds a ``weight``
annotation to tag objects::

    # myapp/view.py
    def tag_cloud(request):
        ...
        tags = MyModel.tags.tag_model.objects.weight()
        ...

The weight field will be a number between ``TAGULOUS_WEIGHT_MIN`` and
``TAGULOUS_WEIGHT_MAX`` (see `Settings`_), although these can be overridden by
passing arguments to it for new min and max values, eg::

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
