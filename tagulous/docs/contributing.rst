.. _contributing:

Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues
and project `roadmap <CHANGES>`_ to see what needs work.

When submitting UI changes, please aim to support the latest versions of
Chrome, Firefox and Internet Explorer through progressive enhancement - old
browsers must still be able to access all functionality.


Testing
-------

It is greatly appreciated when contributions come with unit tests.

Run the python tests using django's test framework::
    ./manage.py test tagulous

Run the javascript tests using Jasmine::
    pip install jasmine
    cd tagulous/tests
    jasmine
    # open http://127.0.0.1:8888/ in your browser

Python tests use ``tagulous.tests_app`` to define test models; javascript
tests are defined in ``tagulous/tests/spec/javascripts/*.spec.js``.


Code overview
-------------

Tag model fields start in ``tagulous.models.fields``; when they are added to
models, the models call the field's ``contribute_to_class`` method, which adds
the descriptors in ``tagulous.models.descriptors`` onto the model in their
place. These descriptors act as getters and setters, channelling data to and
from the managers in ``tagulous.models.managers``.

Model fields take their arguments and store them in
``tagulous.models.options.TagOptions`` instances; initial tags can be loaded
into the database using the functions in ``tagulous.models.initial``, which
is the same code the ``initial_tags`` management command uses.

When a ``ModelForm`` is created for a model with a tag field, the model field's
``formfield`` method is called. This creates a tag form field, defined in
``tagulous.forms``, which is passed the ``TagOptions`` from the model. A
tag form field can also be created directly on a plain form. Tag form fields
in turn uses tag widgets (also in ``tagulous.forms``) to render the field to
HTML with the data from ``TagOptions``.

Tag strings are parsed and rendered (tags joined back to a tag string) by the
functions in ``tagulous.utils``.

Everything for enhancing the admin site with support for tag fields is in
``tagulous.admin``. It is in two sections; registration (which adds tag field
functionality to normal ``ModelAdmin``s, and replaces the widgets with tag
widgets) and tag model admin (for managing tag models).

