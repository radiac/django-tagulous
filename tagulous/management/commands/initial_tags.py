from django.apps import apps
from django.core.management.base import BaseCommand

from ...models.initial import field_initialise_tags, model_initialise_tags


class Command(BaseCommand):
    """
    Load initial tagulous tags
    Optional argument allows you to specify what to load
    If field_name is missing, initialise all tag fields on the model
    If model_name is missing, initialise all tag fields on models in the app
    If app_name is missing, initialise all tag fields on all models in all apps
    """

    help = "Load initial tagulous tags"

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            type=str,
            default="",
            help="Target to load: [<app_name>[.<model_name>[.<field_name>]]]",
        )

    def handle(self, target="", **options):
        # Split up target argument
        parts = target.split(".")
        app_name, model_name, field_name = parts + ([None] * (3 - len(parts)))

        # Look up app
        if app_name:
            app = apps.get_app_config(app_name)
        else:
            app = None

        # Look up specific model, or get all models for the app
        if model_name:
            models = [app.get_model(model_name)]
        elif app is None:
            # Get all models for all apps
            models = apps.get_models()
        else:
            models = app.get_models()

        # If field is specified, can finish here
        if field_name:
            model = models[0]
            field = model._meta.get_field(field_name)
            loaded = field_initialise_tags(model, field, report=self.stdout)

            if not loaded:
                self.stdout.write(
                    "Nothing to load for %s.%s.%s\n"
                    % (model._meta.app_label, model.__name__, field.name)
                )
            return

        # Step through all models and load
        for model in models:
            model_initialise_tags(model, report=self.stdout)
