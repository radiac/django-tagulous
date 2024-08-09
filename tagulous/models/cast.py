"""
Manage instance casting
"""

import inspect

# Give all cast classes a name that's unique to Tagulous and not going to clash with any
# names in the originating class module
CAST_CLASS_PREFIX = "TagulousCastTagged"


def get_cast_class(orig_cls, new_base_cls):
    """
    Get or create a class object that has the new base class and the original class as
    base classes, eg

        class NewClass(new_base_cls, orig_cls):
            ...

    The class will be placed in the module of orig_cls
    """
    # Determine name and module for cast class
    orig_module = inspect.getmodule(orig_cls)
    new_cls_name = f"{CAST_CLASS_PREFIX}{orig_cls.__name__}"

    # See if we've already cast this class
    if hasattr(orig_module, new_cls_name):
        new_cls = getattr(orig_module, new_cls_name)
    else:
        # Make a subclass of TaggedQuerySet and the original class
        new_cls = type(new_cls_name, (new_base_cls, orig_cls), {})

        # Add to original module
        new_cls.__module__ = orig_module.__name__
        setattr(orig_module, new_cls_name, new_cls)

    return new_cls


def cast_instance(instance, new_base_cls):
    """
    Change the class of the object to use new_base_cls as a base class
    """
    orig_cls = instance.__class__
    new_cls = get_cast_class(orig_cls, new_base_cls)
    instance.__class__ = new_cls
