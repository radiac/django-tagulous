===============================
Django Tagulous - Fabulous Tags
===============================

A tagging library for Django built on ForeignKey and ManyToManyField, giving
you all their normal power with a sprinkling of tagging syntactic sugar.

* Project site: https://radiac.net/projects/django-tagulous/
* Source code: https://github.com/radiac/django-tagulous
* Documentation: https://django-tagulous.readthedocs.io/
* Changelog: https://django-tagulous.readthedocs.io/en/latest/changelog.html

.. image:: https://img.shields.io/pypi/v/django-tagulous.svg
    :target: https://pypi.org/project/django-tagulous/
    :alt: PyPI

.. image:: https://readthedocs.org/projects/django-tagulous/badge/?version=latest
    :target: https://django-tagulous.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://github.com/radiac/django-tagulous/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/radiac/django-tagulous/actions/workflows/ci.yml
    :alt: Tests

.. image:: https://codecov.io/gh/radiac/django-tagulous/branch/develop/graph/badge.svg?token=5VZNPABZ7E
    :target: https://codecov.io/gh/radiac/django-tagulous
    :alt: Test coverage


Features
========

* Easy to install - simple requirements, **simple syntax**, lots of options
* Based on ForeignKey and ManyToManyField, so it's **easy to query**
* **Autocomplete** support built in, if you want it
* Supports multiple independent tag fields on a single model
* Can be used as a user-customisable CharField with choices
* Supports **trees of nested tags**, for detailed categorisation
* Admin support for managing tags and tagged models

Supports Django 2.2+, on Python 3.6+.


See the `Documentation <https://django-tagulous.readthedocs.io/>`_
for details of how Tagulous works; in particular:

* `Installation <https://django-tagulous.readthedocs.io/en/latest/installation.html>`_
  - how to install Tagulous
* `Example Usage <https://django-tagulous.readthedocs.io/en/latest/usage.html>`_
  - see examples of Tagulous in use
* `Upgrading <https://django-tagulous.readthedocs.io/en/latest/upgrading.html>`_  -
  how to upgrade Tagulous, and see what has changed in the
  `changelog <https://django-tagulous.readthedocs.io/en/latest/changelog.html>`_.
* `Contributing <https://django-tagulous.readthedocs.io/en/latest/contributing.html>`_
  - for how to contribute to Tagulous


Quickstart
==========

Install with ``pip install django-tagulous``, add ``tagulous`` to Django's
``INSTALLED_APPS`` and `define the serializers`__, then start adding tag fields to your
model::

    from django.db import models
    from tagulous.models import SingleTagField, TagField

    class Person(models.Model):
        name = models.CharField(max_length=255)
        title = SingleTagField(initial="Mr, Mrs, Miss, Ms")
        skills = TagField()

You can now set and get them using strings, lists or querysets::

    myperson = Person.objects.create(name='Bob', title='Mr', skills='run, hop')
    # myperson.skills == 'run, hop'
    myperson.skills = ['jump', 'kung fu']
    myperson.save()
    # myperson.skills == 'jump, "kung fu"'
    runners = Person.objects.filter(skills='run')

Behind the scenes your tags are stored in separate models (by default), so
because the fields are based on ``ForeignKey`` and ``ManyToManyField`` more
complex queries are simple::

    qs = MyRelatedModel.objects.filter(
        person__skills__name__in=['run', 'jump'],
    )

As well as this you also get autocompletion in public and admin forms,
automatic slug generation, unicode support, you can build tag clouds easily,
and can nest tags for more complex categorisation.

__ http://radiac.net/projects/django-tagulous/documentation/installation/
