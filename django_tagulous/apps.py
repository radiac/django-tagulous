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
