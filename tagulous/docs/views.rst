.. _views:

Views
=====

Although Tagulous doesn't need any views by default, it does provide generic
views in ``views.py`` to support AJAX autocomplete requests.

``response = autocomplete(request, tag_model)``
    This takes the request object from the dispatcher, and a reference to the
    tag model which this is autocompleting.
    
    It returns an ``HttpResponse`` with mimetype ``application/json``. The
    response content is a JSON-encoded object with one key, ``results``, which
    is a list of tags
    
``response = autocomplete_login(request, tag_model)``
    Same as ``autocomplete``, except is decorated with Django auth's
    ``login_required``.

For an example, see `Autocomplete Views`_.
