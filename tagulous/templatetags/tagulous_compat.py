"""
Backwards and forwards compatibility for template tags
"""
from __future__ import unicode_literals

import django
from django import template


register = template.Library()


from django.template.defaulttags import url as django_url


@register.tag
def url(parser, token):
    """
    Quoted urls, introduced in Django 1.5, available in 1.4+
    """
    return django_url(parser, token)
