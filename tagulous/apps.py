from django.apps import AppConfig


class TagulousConfig(AppConfig):
    name = "tagulous"

    def ready(self):
        from .checks import register_checks
        from .signals.post import register_post_signals

        register_checks()
        register_post_signals()
