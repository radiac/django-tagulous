# /// script
# dependencies = ["nanodjango", "django-tagulous", "django-style"]
# ///
#
# Demonstrates the can_create tag option, which controls whether users can
# create new tags or are restricted to existing ones.
#
# Three approaches are shown:
#
#   category  - can_create=False on the field: always restricted, no new
#               categories can be created via this form
#
#   skill     - can_create=False on the field, but can_create_skill=True on
#               the model class: the model class overrides the field, so new
#               skills can be created (useful to allow creation by default but
#               lock it down on specific instances)
#
#   hobby     - field allows creation (default), but the form sets
#               can_create_hobby=False: new hobbies are blocked when editing
#               an existing participant, allowed when adding a new one
#
# Usage:
#
#   uv run example/create_limit.py
#
from django.db import models
from nanodjango import Django, defer

with defer:
    from django.contrib import admin, messages
    from django.forms import ModelForm
    from django.http import HttpResponseRedirect
    from django.urls import reverse

    import django_tagulous.admin
    import django_tagulous.models

app = Django(
    ADMIN_URL="admin/",
    EXTRA_APPS=["tagulous"],
    SERIALIZATION_MODULES={
        "xml": "django_tagulous.serializers.xml_serializer",
        "json": "django_tagulous.serializers.json",
        "python": "django_tagulous.serializers.python",
        "yaml": "django_tagulous.serializers.pyyaml",
    },
    STYLE_SITE_TITLE="Tagulous can_create example",
    SQLITE_DATABASE="create_limit.sqlite3",
    MIGRATIONS_DIR="create_limit_migrations",
)


# Models


class Participant(models.Model):
    name = models.CharField(max_length=255)

    # can_create=False on the field - new categories are never allowed
    category = django_tagulous.models.SingleTagField(
        initial="Bronze, Silver, Gold",
        can_create=False,
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Restricted to existing categories; new ones cannot be created",
    )

    # can_create=False on the field, overridden to True on the model class -
    # new skills are allowed (model class takes priority over field)
    skill = django_tagulous.models.TagField(
        initial="Python, JavaScript, SQL, HTML, CSS",
        can_create=False,
        space_delimiter=False,
        blank=True,
        help_text="Field says no, model class says yes - new skills are allowed",
    )
    can_create_skill = True

    # No restriction on the field - can_create_hobby=False is set on the form
    # class, so new hobbies are always blocked via this form
    hobby = django_tagulous.models.TagField(
        initial="reading, cooking, cycling, gaming, hiking",
        force_lowercase=True,
        blank=True,
        help_text="Restricted by the form class - new hobbies cannot be created here",
    )

    class Meta:
        verbose_name_plural = "participants"

    def __str__(self):
        return self.name


# Form


class ParticipantForm(ModelForm):
    can_create_hobby = False

    class Meta:
        fields = ["name", "category", "skill", "hobby"]
        model = Participant


# Admin


class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "skill", "hobby")


django_tagulous.admin.register(Participant, ParticipantAdmin)
django_tagulous.admin.register(Participant.category.tag_model)
django_tagulous.admin.register(Participant.skill.tag_model)
django_tagulous.admin.register(Participant.hobby.tag_model)


# Views


@app.path("<int:participant_pk>/", name="edit")
@app.path("", name="index")
def index(request, participant_pk=None):
    if Participant.category.tag_model.objects.count() == 0:
        app.manage(["initial_tags"])

    if participant_pk:
        participant = Participant.objects.get(pk=participant_pk)
        submit_label = "Update"
    else:
        participant = None
        submit_label = "Add"

    if request.POST:
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            participant = form.save()
            messages.success(request, f"Saved {participant.name}")
            return HttpResponseRedirect(reverse("index"))
    else:
        form = ParticipantForm(instance=participant)

    return app.render(
        request,
        "index.html",
        {
            "participants": Participant.objects.all(),
            "categories": Participant.category.tag_model.objects.all(),
            "skills": Participant.skill.tag_model.objects.all(),
            "hobbies": Participant.hobby.tag_model.objects.all(),
            "form": form,
            "form_media": form.media,
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
    <h2>{% if submit_label == "Update" %}Edit{% else %}Add{% endif %} Participant</h2>
    <ul>
      <li><strong>Category</strong>: always restricted - cannot create new categories</li>
      <li><strong>Skill</strong>: field says restricted, model class says allowed - can create new skills</li>
      <li><strong>Hobby</strong>: always restricted - the form class sets <code>can_create_hobby = False</code></li>
    </ul>
    <form method="post">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit">{{ submit_label }}</button>
    </form>
  </section>

  <section>
    <h2>Participants</h2>
    <table>
      <thead>
        <tr>
          <th>name</th>
          <th>category</th>
          <th>skill</th>
          <th>hobby</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {% for participant in participants %}
          <tr>
            <td>{{ participant.name }}</td>
            <td>{{ participant.category }}</td>
            <td>{{ participant.skill }}</td>
            <td>{{ participant.hobby }}</td>
            <td><a href="{% url "edit" participant_pk=participant.pk %}">Edit</a></td>
          </tr>
        {% empty %}
          <tr><td colspan="5">No participants yet - add one above.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Tag models</h2>
    <table>
      <thead>
        <tr><th>field</th><th>tag</th><th>count</th></tr>
      </thead>
      <tbody>
        {% for tag in categories %}
          <tr><td>category</td><td>{{ tag.name }}</td><td>{{ tag.count }}</td></tr>
        {% endfor %}
        {% for tag in skills %}
          <tr><td>skill</td><td>{{ tag.name }}</td><td>{{ tag.count }}</td></tr>
        {% endfor %}
        {% for tag in hobbies %}
          <tr><td>hobby</td><td>{{ tag.name }}</td><td>{{ tag.count }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

{% endblock %}
""",
}

if __name__ == "__main__":
    app.run()
