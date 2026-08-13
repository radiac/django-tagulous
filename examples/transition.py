# /// script
# dependencies = ["nanodjango", "django-tagulous", "django-style"]
# ///
#
# Demonstrate/test the tagulous -> django_tagulous rename's backwards
# compatibility.
#
# Usage:
#
#   uv run example/transition.py
#
from django.db import models
from nanodjango import Django, defer

with defer:
    from django.contrib import admin, messages
    from django.forms import ModelForm
    from django.http import HttpResponseRedirect
    from django.urls import reverse

    from tagulous.models import SingleTagField, TagField
    from tagulous.views import autocomplete

app = Django(
    ADMIN_URL="admin/",
    EXTRA_APPS=["tagulous"],
    SERIALIZATION_MODULES={
        "xml": "django_tagulous.serializers.xml_serializer",
        "json": "django_tagulous.serializers.json",
        "python": "django_tagulous.serializers.python",
        "yaml": "django_tagulous.serializers.pyyaml",
    },
    STYLE_SITE_TITLE="Tagulous transition example",
    SQLITE_DATABASE="transition.sqlite3",
    MIGRATIONS_DIR="transition_migrations",
)


# Models


class Person(models.Model):
    name = models.CharField(max_length=255)
    title = SingleTagField(
        initial="Mr, Mrs",
        help_text="A SingleTagField, imported from the old 'tagulous' name",
        on_delete=models.CASCADE,
    )
    skills = TagField(
        initial="Python, JavaScript, SQL",
        force_lowercase=True,
        blank=True,
        help_text="A TagField, imported from the old 'tagulous' name",
        autocomplete_view="person_skills_autocomplete",
    )

    class Meta:
        verbose_name_plural = "people"


# Form


class PersonForm(ModelForm):
    class Meta:
        fields = ["name", "title", "skills"]
        model = Person


# Admin


class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "skills")


admin.site.register(Person, PersonAdmin)
admin.site.register(Person.title.tag_model)
admin.site.register(Person.skills.tag_model)


# Views


@app.path("api/skills/", name="person_skills_autocomplete")
def skills_autocomplete(request):
    return autocomplete(request, tag_model=Person.skills.tag_model)


@app.path("<int:person_pk>/", name="edit")
@app.path("", name="index")
def index(request, person_pk=None):
    if person_pk:
        person = Person.objects.get(pk=person_pk)
        submit_label = "Update"
    else:
        person = None
        submit_label = "Add"

    if request.POST:
        person_form = PersonForm(request.POST, instance=person)
        if person_form.is_valid():
            person = person_form.save()
            messages.success(request, f"Saved Person {person.pk}")
            return HttpResponseRedirect(reverse("index"))
    else:
        person_form = PersonForm(instance=person)

    return app.render(
        request,
        "index.html",
        {
            "people": Person.objects.all(),
            "titles": Person.title.tag_model.objects.all(),
            "skills": Person.skills.tag_model.objects.all(),
            "person_form": person_form,
            "form_media": person_form.media,
            "submit_label": submit_label,
        },
    )


# Templates

app.templates = {
    "index.html": """
{% extends "base.html" %}

{% block extra_head %}
  {{ form_media.css }}
  {{ form_media.js }}
{% endblock %}

{% block content %}

  <section>
    <p>
      This page's model, form and admin were all built using
      <code>from tagulous.models import ...</code> and
      <code>EXTRA_APPS=["tagulous"]</code> - the pre-rename names -
      to prove the backwards-compatibility shim works end to end.
    </p>
    <h2>{% if submit_label == "Update" %}Edit{% else %}Add{% endif %} Person</h2>
    <form method="post">
      {% csrf_token %}
      {{ person_form.as_p }}
      <button type="submit">{{ submit_label }}</button>
    </form>
  </section>

  <section>
    <h2>People</h2>
    <table>
      <thead>
        <tr>
          <th>pk</th>
          <th>name</th>
          <th>title</th>
          <th>skills</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {% for person in people %}
          <tr>
            <td>{{ person.pk }}</td>
            <td>{{ person.name }}</td>
            <td>{{ person.title }}</td>
            <td>{{ person.skills }}</td>
            <td><a href="{% url "edit" person_pk=person.pk %}">Edit</a></td>
          </tr>
        {% empty %}
          <tr><td colspan="5">No people yet - add one above.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Titles <small>- SingleTagField tag model</small></h2>
    <table>
      <thead>
        <tr><th>name</th><th>slug</th><th>count</th><th>protected</th></tr>
      </thead>
      <tbody>
        {% for tag in titles %}
          <tr>
            <td>{{ tag.name }}</td>
            <td>{{ tag.slug }}</td>
            <td>{{ tag.count }}</td>
            <td>{{ tag.protected }}</td>
          </tr>
        {% empty %}
          <tr><td colspan="4">No titles yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Skills <small>- TagField tag model</small></h2>
    <table>
      <thead>
        <tr><th>name</th><th>slug</th><th>count</th><th>protected</th></tr>
      </thead>
      <tbody>
        {% for tag in skills %}
          <tr>
            <td>{{ tag.name }}</td>
            <td>{{ tag.slug }}</td>
            <td>{{ tag.count }}</td>
            <td>{{ tag.protected }}</td>
          </tr>
        {% empty %}
          <tr><td colspan="4">No skills yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>
{% endblock %}
""",
}

if __name__ == "__main__":
    app.run()
