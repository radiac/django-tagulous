"""
Views for Tagulous example app
"""
from __future__ import unicode_literals

from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import six

from example import models
from example import forms


def index(request):
    """
    Main demo page
    """
    people = models.Person.objects.all()
    titles = models.Person.title.tag_model.objects.all()
    skills = models.Skill.objects.all()
    hobbies = models.Person.hobbies.tag_model.objects.all()

    if request.POST:
        person_form = forms.PersonForm(request.POST)
        if person_form.is_valid():
            person = person_form.save()
            messages.success(request, 'Form saved as Person %d' % person.pk)
            return HttpResponseRedirect(reverse(index))
    else:
        person_form = forms.PersonForm()

    return render(request, 'example/index.html', {
        'title':        'Django Tagulous Example',
        'Person_name':  models.Person.__name__,
        'Title_name':   models.Person.title.tag_model.__name__,
        'Skill_name':   models.Skill.__name__,
        'Hobby_name':   models.Person.hobbies.tag_model.__name__,
        'people':       people,
        'titles':       titles,
        'hobbies':      hobbies,
        'skills':       skills,
        'person_form':  person_form,
        'form_media':   person_form.media,
    })
