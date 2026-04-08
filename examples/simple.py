# /// script
# dependencies = ["nanodjango", "django-tagulous", "django-style"]
# ///
#
# Usage:
#
#   uv run example/simple.py
#
from django.db import models
from nanodjango import Django, defer

with defer:
    from django.contrib import admin, messages
    from django.forms import ModelForm
    from django.http import HttpResponseRedirect
    from django.urls import reverse

    import tagulous.admin
    import tagulous.models
    import tagulous.views

app = Django(
    ADMIN_URL="admin/",
    EXTRA_APPS=["tagulous"],
    SERIALIZATION_MODULES={
        "xml": "tagulous.serializers.xml_serializer",
        "json": "tagulous.serializers.json",
        "python": "tagulous.serializers.python",
        "yaml": "tagulous.serializers.pyyaml",
    },
    STYLE_SITE_TITLE="Tagulous example",
    SQLITE_DATABASE="simple.sqlite3",
    MIGRATIONS_DIR="simple_migrations",
)


# Models


class Skill(tagulous.models.TagTreeModel):
    class TagMeta:
        initial = [
            "Python/Django",
            "Python/Flask",
            "JavaScript/JQuery",
            "JavaScript/Angular.js",
            "Linux/nginx",
            "Linux/uwsgi",
        ]
        space_delimiter = False
        autocomplete_view = "person_skills_autocomplete"


class Person(models.Model):
    name = models.CharField(max_length=255)
    title = tagulous.models.SingleTagField(
        initial="Mr, Mrs",
        help_text="A SingleTagField - a CharField with dynamic choices",
        on_delete=models.CASCADE,
    )
    skills = tagulous.models.TagField(
        Skill,
        help_text="A TagField referencing a TagTreeModel; does not split on spaces",
    )
    hobbies = tagulous.models.TagField(
        initial="eating, coding, gaming",
        force_lowercase=True,
        blank=True,
        help_text="A TagField with an auto-created tag model; splits on spaces and commas",
    )

    class Meta:
        verbose_name_plural = "people"


# Form


class PersonForm(ModelForm):
    class Meta:
        fields = ["name", "title", "skills", "hobbies"]
        model = Person


# Admin


class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "skills", "hobbies")
    list_filter = ("name", "title", "skills", "hobbies")


tagulous.admin.register(Person, PersonAdmin)
tagulous.admin.register(Skill)
tagulous.admin.register(Person.hobbies.tag_model)


class PersonInline(admin.TabularInline):
    model = Person
    extra = 1


class TitleAdmin(admin.ModelAdmin):
    inlines = [PersonInline]


tagulous.admin.register(Person.title.tag_model, TitleAdmin)


# Views


@app.path("api/skills/", name="person_skills_autocomplete")
def skills_autocomplete(request):
    return tagulous.views.autocomplete(request, tag_model=Skill)


@app.path("<int:person_pk>/", name="edit")
@app.path("", name="index")
def index(request, person_pk=None):
    if Skill.objects.count() == 0:
        app.manage(["initial_tags"])

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
            "skills": Skill.objects.all(),
            "hobbies": Person.hobbies.tag_model.objects.all(),
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
          <th>hobbies</th>
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
            <td>{{ person.hobbies }}</td>
            <td><a href="{% url "edit" person_pk=person.pk %}">Edit</a></td>
          </tr>
        {% empty %}
          <tr><td colspan="6">No people yet - add one above.</td></tr>
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
    <h2>Hobbies <small>- TagField tag model</small></h2>
    <table>
      <thead>
        <tr><th>name</th><th>slug</th><th>count</th><th>protected</th></tr>
      </thead>
      <tbody>
        {% for tag in hobbies %}
          <tr>
            <td>{{ tag.name }}</td>
            <td>{{ tag.slug }}</td>
            <td>{{ tag.count }}</td>
            <td>{{ tag.protected }}</td>
          </tr>
        {% empty %}
          <tr><td colspan="4">No hobbies yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Skills <small>- TagTreeModel</small></h2>
    <table>
      <thead>
        <tr>
          <th>name</th>
          <th>label</th>
          <th>level</th>
          <th>parent</th>
          <th>path</th>
          <th>slug</th>
          <th>count</th>
          <th>protected</th>
        </tr>
      </thead>
      <tbody>
        {% for skill in skills %}
          <tr>
            <td>{{ skill.name }}</td>
            <td>{{ skill.label }}</td>
            <td>{{ skill.level }}</td>
            <td>{{ skill.parent }}</td>
            <td>{{ skill.path }}</td>
            <td>{{ skill.slug }}</td>
            <td>{{ skill.count }}</td>
            <td>{{ skill.protected }}</td>
          </tr>
        {% empty %}
          <tr><td colspan="8">No skills yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>
{% endblock %}
""",
}

if __name__ == "__main__":
    app.run()
