===================================
Example project for django-tagulous
===================================

This example project is configured for Django 2.2.

You can see a static demo version of this example app at http://radiac.net/projects/django-tagulous/demo/

To set it up and run the live version in a self-contained virtualenv::

    virtualenv tagulous-example
    cd tagulous-example
    source bin/activate
    pip install "Django>=2.2,<2.3"
    pip install -e git+https://github.com/radiac/django-tagulous.git#egg=django-tagulous
    cd src/django-tagulous/example
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py initial_tags
    python manage.py runserver

You can then visit the example site at http://localhost:8000/
