.. _usage:

Example Usage
=============

Automatic models
----------------

This simple example creates a ``SingleTagField`` (a glorified ``ForeignKey``)
and two ``TagField`` (a typical tag field, using ``ManyToManyField``)::

    from django.db import models
    import tagulous
    
    class Person(models.Model):
        title = tagulous.models.SingleTagField(
            label="Your prefered title",
            initial="Mr, Mrs, Ms",
        )
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField(
            force_lowercase=True,
            max_count=5,
        )
    
* This will create two new models at runtime to store the tags,
  ``_Tagulous_Person_title`` and ``_Tagulous_Person_skills``.
* ``Person.title`` will now act as a ForeignKey to _Tagulous_Person_title
* ``Person.skills`` will now act as a ManyToManyField to _Tagulous_Person_skills

These models will act like normal models, and can be managed in the database
using standard database migration tools or ``syncdb``.

Initial tags need to be loaded into the database with the 
`management command <#Management Commands>` ``initial_tags``::

    # Person.skills.tag_model == _Tagulous_Person_skills
    
    # Set tags on an instance
    instance = Person()
    instance.skills.set_tags('run, "kung fu", jump')
    
    # They're not committed to the database until you save
    instance.save()

    # Get a list of all tags
    tags = Person.skills.tag_model.objects.all()
    
    # Set tags in different ways
    instance.skills = 'run jump'
    print u'%s' % instance.skills   # prints 'run jump'
    instance.skills = ['jump', 'kung fu']
    instance.save()
    
    # Step through the list of instances in the tag model
    for skill in instance.skills.all():
        print u'%s' % skill
        
    # Compare tag fields
    if instance.skills == other.skills:
        return True
        

.. _example_custom_tag_model:

Custom models
-------------

Explicitly specify the tag model::

    import tagulous
    class Hobbies(tagulous.models.TagModel):
        class TagMeta:
            # Options as passed to TagField
            initial = "eating, coding, gaming"
            force_lowercase = True
            autocomplete_view = 'myapp.views.hobbies_autocomplete'
    
    class Person(models.Model):
        name = models.CharField(max_length=255)
        hobbies = tagulous.models.TagField(to=Hobbies)

Options for an explicit tag model must be set in ``TagMeta`` - you cannot pass
them as arguments in tag fields.

See the documentation for `Tag Models`_ to see which field names tagulous
uses internally.


Tag Trees
---------

A tag field can specify ``tree=True`` to use slashes in tag names to denote
children::

    import tagulous
    class Person(models.Model):
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField(
            force_lowercase=True,
            max_count=5,
            tree=True,
        )

 This can also be set in the tag model's ``TagMeta`` object::

    import tagulous
    class Hobbies(tagulous.models.TagTreeModel):
        class TagMeta:
            initial = "food/eating, food/cooking, gaming/football"
            tree = True
            force_lowercase = True
            autocomplete_view = 'myapp.views.hobbies_autocomplete'
    
    class Person(models.Model):
        name = models.CharField(max_length=255)
        hobbies = tagulous.models.TagField(to=Hobbies)

You can add tags as normal, and then query using tree relationships::

    person.hobbies = "food/eating/mexican, sport/football"
    person.save()
    
    # Get all root nodes: "food", "gaming" and "sport"
    root_nodes = Hobbies.objects.filter(parent=None)
    
    # Get the direct children of food: "food/eating", "food/cooking"
    food_children = Hobbies.objects.get(name="food").children.all()
    
    # Get all descendants of food:
    #   "food/eating", "food/eating/mexican", "food/cooking"
    food_children = Hobbies.objects.get(name="food").get_descendants()

See the documentation for `Tag Trees`_ to see a full list of available tree
properties.


Tag URL
-------

A simple example for defining a ``get_absolute_url`` method on a tag model
without needing to create a custom tag model::

    from django.db import models
    from django.core.urlresolvers import reverse
    import tagulous
    
    class Person(models.Model):
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField(
            get_absolute_url=lambda tag: reverse(
                'myapp.views.by_skill', kwargs={'skill_slug': tag.slug}
            ),
        )

The ``get_absolute_url`` method can now be called as normal; for example, from
a template::

    {% for skill in person.skills.all %}
        <a href="{{ skill.get_absolute_url }}">{{ skill.name }}</a>
    {% endfor %}

If you are using a tree, you will want to use the path instead::

    skills = tagulous.models.TagField(
        tree=True,
        get_absolute_url=lambda tag: reverse(
            'myapp.views.by_skill', kwargs={'skill_path': tag.path}
        ),
    )


ModelForms
----------

A ``ModelForm`` with tag fields needs no special treatment::

    from django.db import models, forms
    import tagulous
    
    class Person(models.Model):
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField()
    
    class PersonForm(forms.ModelForm):
        class Meta:
            model = Person


They are used as normal forms, eg with class-based views::

    from django.views.generic.edit import CreateView
    
    class PersonCreate(CreateView):
        model = Person
        fields = ['name', 'skills']


or with view functions::

    def person_create(request, template_name="my_app/person_form.html"):
        form = PersonForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect('home')
        return render(request, template_name, {'form': form})

However, note that because a ``TagField`` is based on a ``ManyToManyField``, if
you save using ``commit=False``, you will need to call ``save_m2m`` to save the
tags::

    class Pet(models.Model):
        owner = models.ForeignKey('auth.User')
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField()
    
    class PetForm(forms.ModelForm):
        class Meta:
            model = Pet
            
    def pet_create(request, template_name="my_app/pet_form.html"):
        form = PetForm(request.POST or None)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            
            # Next line will save all non M2M fields (including SingleTagField)
            pet.save()
            
            # Next line will save any ``TagField`` values
            form.save_m2m()
            
            return redirect('home')
        return render(request, template_name, {'form': form})

As shown above, this only applies to ``TagField`` - a ``SingleTagField`` is
based on ``ForeignKey``, so will be saved without needing ``save_m2m``.


Forms without models
--------------------

Tagulous form fields take tag options as a single ``TagOptions`` object, rather
than as separate arguments as a model form does::

    from django import forms
    import tagulous
    
    class PersonForm(forms.ModelForm):
        title = tagulous.models.SingleTagField(
            autocomplete_tags=['Mr', 'Mrs', 'Ms']
        )
        name = forms.CharField(max_length=255)
        skills = tagulous.models.TagField(
            tag_options=tagulous.models.TagOptions(
                force_lowercase=True,
            ),
            autocomplete_tags=['running', 'jumping', 'judo']
        )

A ``SingleTagField`` will return a string, and a ``TagField`` will return a
list of strings::

    form = PersonForm(data={
        'title':    'Mx',
        'skills':   'Running, judo',
    })
    assert form.is_valid()
    assert form.cleaned_data['title'] == 'Mx'
    assert form.cleaned_data['skills'] == ['running', 'judo']


Autocomplete Views
------------------

To use AJAX to populate your autocomplete using JavaScript, set the tag option
``autocomplete_view`` in your models to a value for ``reverse()``::

    class Person(models.Model):
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField(
            autocomplete_view='person_skills_autocomplete'
        )

You can then use the default autocomplete views directly in your urls::

    import tagulous
    from myapp.models import Person
    urlpatterns = [
        url(
            r'^person/skills/autocomplete/',
            tagulous.views.autocomplete,
            {'tag_model': Person},
            name='person_skills_autocomplete',
        ),
    ]

See the documentation for `Views`_ for more details.


Filtering autocomplete to initial tags only
-------------------------------------------

You may want autocomplete to only list your initial tags, and not those added
by others; Tagulous makes this easy with the ``autocomplete_initial`` field
option::

    class Person(models.Model):
        title = tagulous.models.SingleTagField(
            label="Your prefered title",
            initial="Mr, Mrs, Ms",
            autocomplete_initial=True,
        )

This will embed the initial tags in the HTML tag.


Filtering autocomplete by related fields
----------------------------------------

Using embedded tags
~~~~~~~~~~~~~~~~~~~

This is if you are embedding the tags into the response; if you are using
autocomplete views, see `Autocomplete Views`_.

Filter the ``autocomplete_tags`` queryset after the form initialises::

    from django.db import models, forms
    import tagulous
    
    class Pet(models.Model):
        owner = models.ForeignKey('auth.User')
        name = models.CharField(max_length=255)
        skills = tagulous.models.TagField()
    
    class PetForm(forms.ModelForm):
        def __init__(self, user, *args, **kwargs):
            super(PetForm, self).__init__(*args, **kwargs)
            
            # Filter skills to initial skills, or ones added by this user
            self.fields['skills'].autocomplete_tags = \
                self.fields['skills'].autocomplete_tags.filter_or_initial(
                    pet__owner=user
                ).distinct()
        class Meta:
            model = Pet

Then always call ``PetForm`` with the user as the first argument, for example::

    def add_pet(request):
        form = PetForm(request.user)
        # ...

For more details, see `Filtering tags by related model fields`_ and 
`Filtering autocomplete tags`_.


Filtering an autocomplete view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add a wrapper to filter the queryset before calling the normal ``autocomplete``
view::

    @login_required
    def autocomplete_pet_skills(request):
        return tagulous.views.autocomplete(
            request,
            Pet.skills.tag_model.objects.filter_or_initial(
                pet__owner=user
            ).distinct()
        )

