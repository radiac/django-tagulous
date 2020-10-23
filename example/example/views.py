"""
Views for Tagulous example app
"""
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from . import forms, models


def index(request, person_pk=None):
    """
    Main demo page
    """
    people = models.Person.objects.all()
    titles = models.Person.title.tag_model.objects.all()
    skills = models.Skill.objects.all()
    hobbies = models.Person.hobbies.tag_model.objects.all()

    if person_pk:
        person = models.Person.objects.get(pk=person_pk)
        submit_label = "Update"
    else:
        person = None
        submit_label = "Add"

    if request.POST:
        person_form = forms.PersonForm(request.POST, instance=person)
        if person_form.is_valid():
            person = person_form.save()
            messages.success(request, "Form saved as Person %d" % person.pk)
            return HttpResponseRedirect(reverse(index))
    else:
        person_form = forms.PersonForm(instance=person)

    return render(
        request,
        "example/index.html",
        {
            "title": "Django Tagulous Example",
            "Person_name": models.Person.__name__,
            "Title_name": models.Person.title.tag_model.__name__,
            "Skill_name": models.Skill.__name__,
            "Hobby_name": models.Person.hobbies.tag_model.__name__,
            "people": people,
            "titles": titles,
            "hobbies": hobbies,
            "skills": skills,
            "person_form": person_form,
            "form_media": person_form.media,
            "submit_label": submit_label,
        },
    )
