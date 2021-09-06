===============================
Django Tagulous - Fabulous Tags
===============================

A tagging library for Django built on ForeignKey and ManyToManyField, giving
you all their normal power with a sprinkling of tagging syntactic sugar.

* Project site: http://radiac.net/projects/django-tagulous/
* Source code: https://github.com/radiac/django-tagulous
* Changelog: http://radiac.net/projects/django-tagulous/documentation/changelog/

.. image:: https://img.shields.io/pypi/v/django-tagulous.svg
    :target: https://pypi.org/project/django-tagulous/

.. image:: https://github.com/radiac/django-tagulous/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/radiac/django-tagulous/actions/workflows/ci.yml

.. image:: https://codecov.io/gh/radiac/django-tagulous/branch/develop/graph/badge.svg?token=5VZNPABZ7E
    :target: https://codecov.io/gh/radiac/django-tagulous


Features
========

* Easy to install - simple requirements, **simple syntax**, lots of options
* Based on ForeignKey and ManyToManyField, so it's **easy to query**
* **Autocomplete** support built in, if you want it
* Supports multiple independent tag fields on a single model
* Can be used as a user-customisable CharField with choices
* Supports **trees of nested tags**, for detailed categorisation
* Admin support for managing tags and tagged models

Supports Django 2.2 to 3.2, on Python 3.6 to 3.9.


See the `Documentation <http://radiac.net/projects/django-tagulous/documentation/>`_
for details of how Tagulous works; in particular:

* `Installation <http://radiac.net/projects/django-tagulous/documentation/installation/>`_
  - how to install Tagulous
* `Example Usage <http://radiac.net/projects/django-tagulous/documentation/usage/>`_
  - see examples of Tagulous in use
* `Upgrading <http://radiac.net/projects/django-tagulous/documentation/upgrading/>`_  -
  how to upgrade Tagulous, and see what has changed in the
  `changelog <http://radiac.net/projects/django-tagulous/documentation/changelog/>`_.
* `Contributing <http://radiac.net/projects/django-tagulous/documentation/contributing/>`_
  - for how to contribute to Tagulous, and the planned
  `roadmap <http://radiac.net/projects/django-tagulous/documentation/contributing/#roadmap>`_.


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
