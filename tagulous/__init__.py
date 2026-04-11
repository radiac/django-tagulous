"""
Compatibility shim — the 'tagulous' package has been renamed to 'django_tagulous'.

This shim re-exports everything from 'django_tagulous' so that existing code
continues to work while you migrate. It will be removed in version 3.0.0.

To migrate:

* In ``INSTALLED_APPS``, change ``"tagulous"`` to ``"django_tagulous"``.
  No database migration is needed — the app label remains ``"tagulous"``.
* In Python imports, replace ``import tagulous`` / ``from tagulous import``
  with ``import django_tagulous`` / ``from django_tagulous import``.
"""

import importlib
import sys
import warnings

warnings.warn(
    "The 'tagulous' package has been renamed to 'django_tagulous'. "
    "Update INSTALLED_APPS and your imports to use 'django_tagulous'. "
    "The 'tagulous' compatibility shim will be removed in version 3.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

import django_tagulous as _pkg  # noqa: E402

# Register all submodules as tagulous.* aliases so that
# ``import tagulous.admin``, ``from tagulous.models import …`` etc. all work.
_submodules = [
    "admin",
    "apps",
    "checks",
    "constants",
    "contrib",
    "contrib.drf",
    "forms",
    "management",
    "management.commands",
    "management.commands.initial_tags",
    "models",
    "models.cast",
    "models.descriptors",
    "models.fields",
    "models.initial",
    "models.managers",
    "models.migrations",
    "models.models",
    "models.options",
    "models.tagged",
    "serializers",
    "serializers.base",
    "serializers.json",
    "serializers.python",
    "serializers.pyyaml",
    "serializers.xml_serializer",
    "settings",
    "signals",
    "signals.post",
    "signals.pre",
    "utils",
    "views",
]

for _name in _submodules:
    try:
        _mod = importlib.import_module(f"django_tagulous.{_name}")
        sys.modules[f"tagulous.{_name}"] = _mod
    except ImportError:
        pass

# Replace this shim with django_tagulous itself so that attribute access on
# the ``tagulous`` name (e.g. ``tagulous.models.TagField``) works transparently.
sys.modules["tagulous"] = _pkg
