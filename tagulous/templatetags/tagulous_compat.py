"""
Backwards and forwards compatibility for template tags
"""
import django
from django import template

register = template.Library()


#
# {% url "quoted.view" %}
#
# Django 1.4 provides quote support with {% load url from future %}
# Django 1.7 deprecates future
# Django 1.9 removes future
#

if django.VERSION < (1, 5):
    from django.templatetags.future import url as django_url
else:
    from django.template.defaulttags import url as django_url

@register.tag
def url(parser, token):
    """
    Quoted urls, introduced in Django 1.5, available in 1.4+
    """
    return django_url(parser, token)
