============
Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues to see
what needs work. Tagulous aims to be a comprehensive tagging solution, but try to keep
new features from having a significant impact on people who won't use them (eg tree
support is optional).

When submitting UI changes, please aim to support the latest versions of
Chrome, Firefox and Internet Explorer through progressive enhancement - users
of old browsers must still be able to tag things, even if they don't get all
the bells and whistles.


Installing
==========

The easiest way to work on Tagulous is to fork the project on GitHub, then
install it to a venv::

    python -m venv venv
    source venv/bin/activate
    git clone https://github.com/<username>/django-tagulous.git
    cd django-tagulous
    pip install -r tests/requirements/django-VERSION.txt
    pre-compile install

(replacing ``USERNAME`` with your username and ``VERSION`` with the version of Django
you're working with).

This will install the development dependencies too, and you'll find the
tagulous source ready for you to work on in the ``src`` folder of your
virtual environment.


Testing
=======

It is greatly appreciated when contributions come with unit tests.

Pytest is the test runner of choice::

    pytest
    pytest tests/test_file.py
    pytest tests/test_file::TestClass::test_method

Use ``tox`` to run them on one or more supported versions, eg::

    tox [-e py3.12-django4.2]

To use a different database (mysql, postgres etc) use the environment variables
``DATABASE_ENGINE``, ``DATABASE_NAME``, ``DATABASE_USER``,
``DATABASE_PASSWORD``,  ``DATABASE_HOST`` and ``DATABASE_PORT``, eg::

    DATABASE_ENGINE=pgsql DATABASE_NAME=tagulous_test [...] tox

Most Tagulous python modules have corresponding test modules, with test classes
which subclass ``tests.lib.TagTestManager``. They use test apps defined under
the ``tests`` dir where required.

Run the javascript tests using Jasmine::

    pip install jasmine
    cd tests
    jasmine
    # open http://127.0.0.1:8888/ in your browser

Javascript tests are defined in ``tests/spec/javascripts/*.spec.js``.


Adding a Django version
-----------------------

We have a separate requirements file for each version of Django, as some dependencies
specify a minimum version of Django.

* Add a requirements file to ``tests/requirements/django-<version>.in``
* Build the pinned requirements with ``cd tests/requirements && pip-compile && cd -``
* Update ``tox.ini`` - change ``envlist`` and ``deps``
* Update the three ``matrix`` definitions in ``.github/workflows/ci.yml``


Code overview
=============

Tag model fields start in :gitref:`tagulous/models/fields.py`; when they are
added to models, the models call the field's ``contribute_to_class`` method,
which adds the descriptors in :gitref:`tagulous/models/descriptors.py` onto
the model in their place. These descriptors act as getters and setters,
channeling data to and from the managers in
:gitref:`tagulous/models/managers.py`.

Models which have tag fields are called tagged models. For tags to be fully
supported in constructors, managers and querysets, those classes need to use
the classes defined in :gitref:`tagulous/models/tagged.py` as base classes.
That file contains a ``class_prepared`` signal listener which tries to
dynamically change the base classes of any models which contain tag fields.

Model fields take their arguments and store them in a ``TagOptions`` instance,
defined in :gitref:`tagulous/models/options.py`. Any ``initial`` tags in the
options can be loaded into the database using the functions in
:gitref:`tagulous/models/initial.py`, which is the same code the
``initial_tags`` management command uses.

When a ``ModelForm`` is created for a model with a tag field, the model field's
``formfield`` method is called. This creates a tag form field, defined in
:gitref:`tagulous/forms.py`, which is passed the ``TagOptions`` from the model.
A tag form field can also be created directly on a plain form. Tag form fields
in turn uses tag widgets (also in :gitref:`tagulous/forms.py`) to render the
field to HTML with the data from ``TagOptions``.

Tag strings are parsed and rendered (tags joined back to a tag string) by the
functions in :gitref:`tagulous/utils.py`.

Everything for enhancing the admin site with support for tag fields is in
:gitref:`tagulous/admin.py`. It is in two sections; registration (which adds
tag field functionality to a normal ``ModelAdmin``, and replaces the widgets
with tag widgets) and tag model admin (for managing tag models).
