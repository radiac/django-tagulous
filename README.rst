===============================
Django Tagulous - Fabulous Tags
===============================

A tagging library for Django built on ForeignKey and ManyToManyField, giving
you all their normal power with a sprinkling of tagging syntactic sugar.

* Project site: http://radiac.net/projects/django-tagulous/
* Source code: https://github.com/radiac/django-tagulous

.. image:: https://travis-ci.org/radiac/django-tagulous.svg?branch=master
    :target: https://travis-ci.org/radiac/django-tagulous

.. image:: https://coveralls.io/repos/radiac/django-tagulous/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/radiac/django-tagulous?branch=master

Features
========

* Easy to install - simple requirements, simple syntax, lots of options
* Based on ForeignKey and ManyToManyField, so it's easy to query
* Autocomplete support built in, if you want it
* Supports multiple independent tag fields on a single model
* Can be used as a user-customisable CharField with choices
* Supports trees of nested tags, for detailed categorisation
* Admin support for managing tags and tagged models

Version 0.12.0; supports Django 1.4.2 to 1.10, on Python 2.7 to 3.5.

See the `Documentation <http://radiac.net/projects/django-tagulous/documentation/>`_
for details of how Tagulous works; in particular:

* `Installation <http://radiac.net/projects/django-tagulous/documentation/installation/>`_
  - how to install Tagulous
* `Example Usage <http://radiac.net/projects/django-tagulous/documentation/usage/>`_
  - see examples of Tagulous in use
* `Upgrading <http://radiac.net/projects/django-tagulous/documentation/upgrading/>`_  - how to upgrade Tagulous, and see what has changed in the
  `changelog <http://radiac.net/projects/django-tagulous/documentation/upgrading/#changelog>`_.
* `Contributing <http://radiac.net/projects/django-tagulous/documentation/contributing/>`_
  - for how to contribute to Tagulous, and the planned
  `roadmap <http://radiac.net/projects/django-tagulous/documentation/contributing/#roadmap>`_.


Quickstart
==========

Install with ``pip install django-tagulous``, add ``tagulous`` to Django's
``INSTALLED_APPS``, then start adding tag fields to your model::

    from django.db import models
    import tagulous

    class Person(models.Model):
        name = models.CharField(max_length=255)
        title = tagulous.models.SingleTagField(initial="Mr, Mrs, Miss, Ms")
        skills = tagulous.models.TagField()

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
