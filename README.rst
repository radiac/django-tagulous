===============================
Django Tagulous - Fabulous Tags
===============================

A tagging library for Django built on ForeignKey and ManyToManyField, giving
you all their normal power with a sprinkling of tagging syntactic sugar.

http://radiac.net/projects/django-tagulous/

.. image:: https://travis-ci.org/radiac/django-tagulous.svg?branch=master
    :target: https://travis-ci.org/radiac/django-tagulous


Features
========

* Easy to install - simple requirements, simple syntax, lots of options
* Based on ForeignKey and ManyToManyField, so it's easy to query
* Autocomplete support built in, if you want it
* Supports multiple independent tag fields on a single model
* Can be used as a user-customisable CharField with choices
* Supports trees of nested tags, for detailed categorisation
* All the other features you'd expect a tagging library to have

Version 0.7.0; requires Django 1.4 or later.

* See `Documentation <docs/index.rst>`_ for details of how it all works
* See `Example Usage <docs/usage.rst>`_ to see examples of it in use
* See `CHANGES <CHANGES>`_ for full changelog and roadmap
* See `Upgrading <docs/upgrading.rst>`_ when upgrading an existing Tagulous
  installation


Quickstart
==========

Install ``django-tagulous``, add ``tagulous`` to ``INSTALLED_APPS``, then start
adding tag fields to your model::

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
