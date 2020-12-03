from django.apps import AppConfig


class TagulousConfig(AppConfig):
    name = "tagulous"

    def ready(self):
        from .signals.post import register_post_signals

        register_post_signals()
