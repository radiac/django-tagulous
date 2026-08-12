from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query import QuerySet
from django_dropulous.views import AutocompleteView

from .models.models import TagModelBase


class TagulousAutocompleteView(AutocompleteView):
    """
    Autocomplete view for tag fields

    Register it once per tag field/model, passing ``tag_model`` as an extra url
    kwarg exactly as the legacy ``autocomplete()`` view expected it:

        tag_model
            Reference to the tag model (eg MyModel.tags.tag_model), or a
            queryset of the tag model (eg MyModel.tags.tag_model.objects.all())

    The response also honours the ``p`` (page) GET parameter select2 already
    sends, so pagination keeps working via that adaptor - Dropulous itself
    doesn't yet request further pages (``more`` is just a hint for now), so
    this is here ready for when it does, without needing to change again.
    """

    _tag_model: TagModelBase = None

    @property
    def tag_model(self):
        if self._tag_model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'tag_model' to be set, "
                "either as a class attribute or via as_view(tag_model=...)"
            )
        return self._tag_model

    @tag_model.setter
    def tag_model(self, value):
        self._tag_model = value

    def get(self, request, *args, **kwargs):
        if isinstance(self.tag_model, QuerySet):
            self.queryset = self.tag_model
            self.tag_model = self.tag_model.model
        else:
            self.queryset = self.tag_model.objects
        return super().get(request, *args, **kwargs)

    @property
    def limit(self):
        return self.tag_model.tag_options.autocomplete_limit

    def get_options(self, query):
        options = self.tag_model.tag_options
        queryset = self.queryset

        if query:
            if options.force_lowercase:
                query = query.lower()
            lookup = "contains" if options.autocomplete_view_fulltext else "startswith"
            if not (self.case_sensitive or options.case_sensitive):
                lookup = f"i{lookup}"
            queryset = queryset.filter(**{f"name__{lookup}": query})

        # Paging itself is handled generically by AutocompleteView.collect_options(),
        # based on self.page - just return the full ordered queryset here
        return queryset.order_by("name").values_list("name", "name")

    def is_valid_value(self, value):
        return self.queryset.filter(name=value).exists()


# Legacy fbvs


def autocomplete(request, tag_model):
    """
    Arguments:
        request
            The request object from the dispatcher
        tag_model
            Reference to the tag model (eg MyModel.tags.tag_model), or a
            queryset of the tag model (eg MyModel.tags.tag_model.objects.all())

    The following GET parameters can be set:
        q   The query string to filter by (match against start of string)
        p   The current page

    Response is a JSON object with following keys:
        results     List of tags
        more        Boolean if there is more
    }
    """
    return TagulousAutocompleteView.as_view(tag_model=tag_model)(request)


@login_required
def autocomplete_login(*args, **kwargs):
    return autocomplete(*args, **kwargs)
