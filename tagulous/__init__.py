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
from importlib.machinery import ModuleSpec

warnings.warn(
    "The 'tagulous' package has been renamed to 'django_tagulous'. "
    "Update INSTALLED_APPS and your imports to use 'django_tagulous'. "
    "The 'tagulous' compatibility shim will be removed in version 3.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

import django_tagulous as _pkg  # noqa: E402


class _TagulousAliasFinder:
    """
    Resolve ``tagulous.<name>`` imports as aliases for ``django_tagulous.<name>``.

    Import as required to avoid import-time errors
    """

    prefix = "tagulous."

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(self.prefix):
            return None
        return ModuleSpec(fullname, self, is_package=True)

    def create_module(self, spec):
        real_name = "django_tagulous." + spec.name[len(self.prefix) :]
        return importlib.import_module(real_name)

    def exec_module(self, module):
        pass


sys.meta_path.insert(0, _TagulousAliasFinder())

# Replace this shim with django_tagulous itself so that attribute access on
# the ``tagulous`` name (e.g. ``tagulous.models.TagField``) works transparently.
sys.modules["tagulous"] = _pkg
