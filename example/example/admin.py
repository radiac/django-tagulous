from __future__ import unicode_literals

from django.contrib import admin
from django.utils import six

import tagulous.admin

from example import models


# Register the Person with a custom ModelAdmin
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'skills', 'hobbies')
    list_filter = ('name', 'title', 'skills', 'hobbies')
tagulous.admin.register(models.Person, PersonAdmin)

# Auto-gen the ModelAdmins for skills and hobbies
tagulous.admin.register(models.Skill)
tagulous.admin.register(models.Person.hobbies.tag_model)

# Give the Title ModelAdmin the people as inlines
class PersonInline(admin.TabularInline):
    model = models.Person
    extra = 3

class TitleAdmin(admin.ModelAdmin):
    inlines = [PersonInline]
tagulous.admin.register(models.Person.title.tag_model, TitleAdmin)
