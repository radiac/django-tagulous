from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import simplejson

@login_required
def autocomplete_login(*args, **kwargs):
    return autocomplete(*args, **kwargs)

def autocomplete(request, tag_model):
    """
    Arguments:
        request
            The request object from the dispatcher
        tag_model
            Reference to the tag model (eg myModel.tags.model)
            
    JSON object returned:
    {
        results:    []
    }
    """
    # Get tag options
    options = tag_model.tag_options
    
    # Get query string
    query = request.GET.get('q', '')
    
    # Perform search
    if query:
        if options.force_lowercase:
            query = query.lower()
            
        if options.case_sensitive:
            results = tag_model.objects.filter(name__startswith=query)
        else:
            results = tag_model.objects.filter(name__istartswith=query)
    else:
        results = tag_model.objects.all()
    
    # Limit results
    if options.autocomplete_limit:
        results = results.order_by('name')[:options.autocomplete_limit]
    
    # Build response
    response = {
        'results':  [tag.name for tag in results],
    }
    return HttpResponse(
        simplejson.dumps(response), mimetype='application/json'
    )
    