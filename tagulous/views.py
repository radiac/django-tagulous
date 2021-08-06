import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.query import QuerySet
from django.http import HttpResponse


@login_required
def autocomplete_login(*args, **kwargs):
    return autocomplete(*args, **kwargs)


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
    # Get model, queryset and tag options
    if isinstance(tag_model, QuerySet):
        queryset = tag_model
        tag_model = queryset.model
    else:
        queryset = tag_model.objects
    options = tag_model.tag_options

    # Get query string
    query = request.GET.get("q", "")
    page = int(request.GET.get("p", 1))

    # Perform search
    if query:
        if options.force_lowercase:
            query = query.lower()

        if options.autocomplete_view_fulltext:
            lookup = "contains"
        else:
            lookup = "startswith"

        if not options.case_sensitive:
            lookup = f"i{lookup}"

        results = queryset.filter(**{f"name__{lookup}": query})

    else:
        results = queryset.all()

    # Limit results
    if options.autocomplete_limit:
        start = options.autocomplete_limit * (page - 1)
        end = options.autocomplete_limit * page
        more = results.count() > end
        results = results.order_by("name")[start:end]

    # Build response
    response = {"results": [tag.name for tag in results], "more": more}
    return HttpResponse(
        json.dumps(response, cls=DjangoJSONEncoder), content_type="application/json"
    )
