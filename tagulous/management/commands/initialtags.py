from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from django.db.models import get_app, get_models

import tagulous


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
            models = [getattr(app, model_name)]
        else:
            models = get_models(app)
        
        # If field is specified, can finish here
        if field_name:
            model = models[0]
            field = model._meta.get_field_by_name(field_name)[0]
            loaded = self.initialise_tag(model, field)
            
            if not loaded:
                print "Nothing to load for %s.%s.%s" % (
                    model._meta.app_label,
                    model.__name__,
                    field.name,
                )
            return
            
        # Step through all fields on all models
        for model in models:
            for field in model._meta.fields + model._meta.many_to_many:
                if isinstance(
                    field,
                    (tagulous.SingleTagField, tagulous.TagField)
                ):
                    self.initialise_tag(model, field)

    def initialise_tag(self, model, field):
        if not field.tag_options.initial:
            return False
            
        print "Loading initial tags for %s.%s.%s" % (
            model._meta.app_label,
            model.__name__,
            field.name,
        )
        
        descriptor = getattr(model, field.name)
        descriptor.load_initial()
        return True
        