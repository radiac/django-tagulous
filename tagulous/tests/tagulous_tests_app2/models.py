"""
Test models
"""

from django.db import models

import tagulous

class MixedModel(models.Model):
    """
    For testing mixed model in a separate app
    """
    name = models.CharField(blank=True, max_length=100)
    singletag = tagulous.models.SingleTagField(
        blank=True, null=True, initial='Mr, Mrs, Ms',
    )
    tags = tagulous.models.TagField(
        blank=True, null=True, initial='Adam, Brian, Chris',
    )
