"""
Tag options
"""

from .. import constants
from .. import settings as tag_settings
from ..utils import parse_tags, render_tags


class TagOptions(object):
    """
    Simple class container for tag options
    """

    def __init__(self, **kwargs):
        """
        Set up tag options using defaults, overridden by keyword arguments
        """
        self.update(kwargs)

    def update(self, options):
        """
        Update this TagOptions in place with options from a dict or TagOptions
        """
        # Ensure a dict
        if isinstance(options, TagOptions):
            options = options.items(with_defaults=False)

        for key, val in options.items():
            setattr(self, key, val)

        return self

    def set_missing(self, options):
        """
        Update this TagOptions in place with options from a dict or TagOptions,
        but only where the keys are not already set on this TagOptions

        Similar to opt1 = opt2 + op1, only changes in place
        """
        # Ensure a dict
        if isinstance(options, TagOptions):
            options = options.items(with_defaults=False)

        # Get currently set keys
        items = self.items(with_defaults=False)
        for key, val in options.items():
            if key not in items:
                setattr(self, key, val)

        return self

    def contribute_to_class(self, cls, name):
        """
        Add to class
        """
        setattr(cls, name, self)

    def __setattr__(self, name, value):
        """
        Only allow an option to be set if it's valid
        """
        if name == "initial":
            # Store as a list of strings, with the tag string available on
            # initial_string for migrations
            if value is None:
                self.__dict__["initial_string"] = ""
                self.__dict__["initial"] = []
            elif isinstance(value, str):
                self.__dict__["initial_string"] = value
                self.__dict__["initial"] = parse_tags(value)
            else:
                self.__dict__["initial_string"] = render_tags(value)
                self.__dict__["initial"] = value

        elif name in constants.OPTION_DEFAULTS:
            self.__dict__[name] = value
        else:
            raise AttributeError(name)

    def __getattr__(self, name):
        """
        Fall back to default options if it's not set

        Requests for locally-defined properties will be fielded directly by
        __dict__
        """
        if name == "initial_string":
            # If here, there is no initial set in the __dict__
            # There is nothing in defaults to fall back to either
            return ""
        if name not in constants.OPTION_DEFAULTS:
            raise AttributeError(name)
        return self.__dict__.get(name, tag_settings.DEFAULT_TAG_OPTIONS[name])

    def _get_items(self, with_defaults, keys):
        """
        Return a dict of options specified in keys, with defaults if required
        """
        if with_defaults:
            return dict(
                [
                    (
                        name,
                        self.__dict__.get(name, tag_settings.DEFAULT_TAG_OPTIONS[name]),
                    )
                    for name in keys
                ]
            )

        return dict(
            [(name, value) for name, value in self.__dict__.items() if name in keys]
        )

    def items(self, with_defaults=True):
        """
        Get a dict of all options

        If with_defaults is True, any missing options will be set to their
        defaults; if False, missing options will be omitted.
        """
        return self._get_items(with_defaults, constants.OPTION_DEFAULTS)

    def form_items(self, with_defaults=True):
        """
        Get a dict of all options in FORM_OPTIONS, suitable for rendering
        into the data-tag-options attribute of the field HTML.

        If with_defaults is True, any missing options will be set to their
        defaults; if False, missing options will be omitted.
        """
        return self._get_items(with_defaults, constants.FORM_OPTIONS)

    def clone(self):
        """
        Return a new TagOptions object with the options set on this object.
        """
        dct = self.items(with_defaults=False)
        return TagOptions(**dct)

    def __add__(self, options):
        """
        Return a new TagOptions object with the options set on this object,
        overridden by any on the second specified TagOptions object.
        """
        dct = self.items(with_defaults=False)
        dct.update(options.items(with_defaults=False))
        return TagOptions(**dct)
