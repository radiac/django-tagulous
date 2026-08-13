# Django Tagulous - Fabulous Tags


[![PyPI](https://img.shields.io/pypi/v/django-tagulous.svg)](https://pypi.org/project/django-tagulous/)
[![Documentation](https://readthedocs.org/projects/django-tagulous/badge/?version=latest)](https://django-tagulous.readthedocs.io/en/latest/)
[![Tests](https://github.com/radiac/django-tagulous/actions/workflows/ci.yml/badge.svg)](https://github.com/radiac/django-tagulous/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/radiac/django-tagulous/graph/badge.svg?token=zotfCDdrUG)](https://codecov.io/gh/radiac/django-tagulous)

A tagging library for Django. Built on ForeignKey and ManyToManyField to support tag
strings as well as native ORM queries.

Use a `SingleTagField` as a CharField with dynamic choices, or a `TagField` for
conventional tagging or nested categorisation.

* [Project site](https://radiac.net/projects/django-tagulous/)
* [Source code](https://github.com/radiac/django-tagulous)
* [Documentation](https://django-tagulous.readthedocs.io/)
* [Live demo](https://radiac-django-tagulous-demo.nanodjango.dev)
* [Changelog](https://django-tagulous.readthedocs.io/en/latest/changelog/)

If you find this project useful, please do consider [sponsoring development](https://github.com/sponsors/radiac).


## Features

* Easy to install - simple requirements, **simple syntax**, lots of options
* Based on ForeignKey and ManyToManyField, so it's **easy to query**
* **Autocomplete** support built in, if you want it
* Supports multiple **independent fields** on a single model
* Supports **trees of nested tags**, for detailed categorisation
* Admin support for managing tags and tagged models

Tested on Django 3.2 to 6.1, on Python 3.10+.


See the [Documentation](https://django-tagulous.readthedocs.io/)
for details of how Tagulous works; in particular:

* [Installation](https://django-tagulous.readthedocs.io/en/latest/installation/) -
  how to install Tagulous
* [Example Usage](https://django-tagulous.readthedocs.io/en/latest/usage/) -
  see examples of Tagulous in use
* [Upgrading](https://django-tagulous.readthedocs.io/en/latest/upgrading/) -
  how to upgrade Tagulous, and see what has changed in the
  [changelog](https://django-tagulous.readthedocs.io/en/latest/changelog/)
* [Contributing](https://django-tagulous.readthedocs.io/en/latest/contributing/) -
  for how to contribute to Tagulous


Quickstart
==========

Install with `pip install django-tagulous`, add `django_tagulous` to Django's `INSTALLED_APPS`
and
[define the serializers](https://django-tagulous.readthedocs.io/en/latest/installation/),
then start adding tag fields to your model:

```python
from django.db import models
from django_tagulous.models import SingleTagField, TagField

class Person(models.Model):
    name = models.CharField(max_length=255)
    title = SingleTagField(initial="Mr, Mrs, Miss, Ms")
    skills = TagField()
```

You can now set and get them using strings, lists or querysets:

```python
myperson = Person.objects.create(name='Bob', title='Mr', skills='run, hop')
# myperson.skills == 'run, hop'
myperson.skills = ['jump', 'kung fu']
myperson.save()
# myperson.skills == 'jump, "kung fu"'
runners = Person.objects.filter(skills='run')
```

Behind the scenes each tag field is a `ForeignKey` or `ManyToManyField` relationship to
a separate model (by default), so more complex queries are simple:

```python
qs = MyRelatedModel.objects.filter(
    person__skills__name__in=['run', 'jump'],
)
```

As well as this you also get autocompletion in public and admin forms,
automatic slug generation, unicode support, you can build tag clouds easily,
and can nest tags for more complex categorisation.
