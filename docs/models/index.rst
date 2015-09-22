======
Models
======

Tagulous provides two new :doc:`model fields <fields>` - :ref:`model_tagfield`
and :ref:`model_singletagfield`, which you use to add tags to your existing
models to make them :doc:`tagged models <tagged_models>`. They provide extra
tag-related functionality.

They can also be queried like a normal Django ``ForeignKey`` or
``ManyToManyField``, but with extra :ref:`query enhancements <querying>` to
make working with tags easier.

Tags are stored in :doc:`tag model <tag_models>` subclasses, which can either
be unique to each different tag field, or can be shared between them. If you
don't specify a tag model on your field definition, one will be created for you
automatically.

Tags can be nested using :doc:`tag trees <tag_trees>`. There is also support
for :doc:`database migrations <migrations>`.


.. toctree::
    :maxdepth: 2

    fields
    tag_models
    tag_trees
    tagged_models
    migrations


