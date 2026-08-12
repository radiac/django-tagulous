from pathlib import Path

from django.apps import AppConfig


class TagulousConfig(AppConfig):
    name = "django_tagulous"
    label = "tagulous"  # preserve existing database table names

    def ready(self):
        from .checks import register_checks
        from .signals.post import register_post_signals

        register_checks()
        register_post_signals()
        self._enhance_forms()
        self._enhance_admin()
        self._register_dropulous_static()

    def _enhance_forms(self):
        from . import settings as tag_settings

        if not tag_settings.ENHANCE:
            return

        from django.forms.forms import Form
        from django.forms.models import BaseModelForm

        from .forms import TagFormMixin

        if TagFormMixin not in Form.__bases__:
            Form.__bases__ = (TagFormMixin,) + Form.__bases__
        if TagFormMixin not in BaseModelForm.__bases__:
            BaseModelForm.__bases__ = (TagFormMixin,) + BaseModelForm.__bases__

    def _enhance_admin(self):
        from . import settings as tag_settings

        if not tag_settings.ENHANCE:
            return

        try:
            from .admin import enhance
        except ImportError:
            return  # django.contrib.admin not installed

        enhance()

    def _register_dropulous_static(self):
        """
        Inject django-dropulous's static files into STATICFILES_DIRS if necessary

        All we need from django-dropulous is its static files, and we don't want to
        complicate our installation/upgrade instructions by asking users to add
        django_dropulous to INSTALLED_APPS just for us, so we'll add its static files to
        STATICFILES_DIRS when tagulous loads.
        """
        from django.conf import settings

        if "django_dropulous" in settings.INSTALLED_APPS:
            # Already registered normally, nothing to do
            return

        import django_dropulous

        static_dir = Path(django_dropulous.__file__).resolve().parent / "static"
        if static_dir not in settings.STATICFILES_DIRS:
            settings.STATICFILES_DIRS = [*settings.STATICFILES_DIRS, static_dir]
