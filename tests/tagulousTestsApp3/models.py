"""
Test models for capitalised app names (#60)
"""
from django.db import models

import tagulous


class CapitalisedTest(models.Model):
    """
    For tests which need a capitalised table name
    """

    name = models.CharField(max_length=10)
    singletag = tagulous.models.SingleTagField(blank=True)
    tags = tagulous.models.TagField(blank=True)
