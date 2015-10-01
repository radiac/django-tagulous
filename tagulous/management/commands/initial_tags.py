from __future__ import unicode_literals

from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from django.utils import six

# Abstract model lookup for django compatibility
try:
    # Django 1.8 and later
    from django.apps import apps
except ImportError:
    # Django 1.7 or earlier
    from django.db.models import get_app, get_models
    get_model = lambda app, model_name: getattr(app, model_name)
else:
    get_app = apps.get_app_config
    get_models = lambda app: app.get_models() if app else apps.get_models()
    get_model = lambda app, model_name: app.get_model(model_name)


from tagulous.models.initial import field_initialise_tags, model_initialise_tags


class Command(BaseCommand):
    """
    Load initial tagulous tags
    Optional argument allows you to specify what to load
    If field_name is missing, initialise all tag fields on the model
    If model_name is missing, initialise all tag fields on models in the app
    If app_name is missing, initialise all tag fields on all models in all apps
    """
    help = 'Load initial tagulous tags'
    args = '[<app_name>[.<model_name>[.<field_name>]]]'

    def handle(self, target='', **options):
        # Split up target argument
        parts = target.split('.')
        app_name, model_name, field_name = parts + ([None] * (3 - len(parts)))
        
        # Look up app
        if app_name:
            app = get_app(app_name)
        else:
            # get_models(None) will get all models
            app = None
        
        # Look up specific model, or get all models for the app
        if model_name:
            models = [get_model(app, model_name)]
        else:
            models = get_models(app)
        
        # If field is specified, can finish here
        if field_name:
            model = models[0]
            field = model._meta.get_field(field_name)
            loaded = field_initialise_tags(
                model, field, report=self.stdout,
            )
            
            if not loaded:
                self.stdout.write("Nothing to load for %s.%s.%s\n" % (
                    model._meta.app_label,
                    model.__name__,
                    field.name,
                ))
            return
        
        # Step through all models and load
        for model in models:
            model_initialise_tags(model, report=self.stdout)
