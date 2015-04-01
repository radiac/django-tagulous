.. _usage:

Example Usage
=============

Automatic models
----------------

This simple example creates a ``SingleTagField`` (a glorified ``ForeignKey``)
and two ``TagField``s (a typical tag field, using ``ManyToManyField``).

    from django.db import models
    import tagulous
    
    class Person(models.Model):
        title = tagulous.SingleTagField(initial="Mr, Mrs, Miss, Ms")
        name = models.CharField(max_length=255)
        skills = tagulous.TagField()
    
* This will create two new models at runtime to store the tags,
  ``_Tagulous_Person_title`` and ``_Tagulous_Person_skills``.
* ``Person.title`` will now act as a ForeignKey to _Tagulous_Person_title
* ``Person.skills`` will now act as a ManyToManyField to _Tagulous_Person_skills

These models will act like normal models, and can be managed in the database
using standard database migration tools or ``syncdb``.

Initial tags need to be loaded into the database with the 
`management command <#Management Commands>` ``initial_tags``.

    # Person.skills.tag_model == _Tagulous_Person_skills
    
    # Set tags on an instance
    instance = Person()
    instance.skills.set_tags('run, "kung fu", jump')
    
    # Save the changes to the database
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
        

:: _example_custom_tag_model:

Custom models
-------------

Explicitly specify the tag model

    import tagulous
    class Hobbies(tagulous.TagModel):
        # All custom tag models must provide a ``name`` CharField. This is what
        # the tag will be shown as and parsed using.
        name = CharField()
        
        # Custom tag fields
        # These must all be allowed to be blank
        started = DateField(blank=True)
        
        class TagMeta:
            # Options as passed to TagField
            initial = "eating, coding, gaming"
            force_lowercase = True
            autocomplete_view = 'myapp.views.hobbies_autocomplete'
    
    class Person(models.Model):
        ...
        hobbies = tagulous.TagField(to=Hobbies, autocomplete_view=None)


Forms
-----

# ++ Add forms


Autocomplete Views
------------------

# ++ Add examples
