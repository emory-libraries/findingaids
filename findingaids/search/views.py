from django.shortcuts import render_to_response
from findingaids.fa.models import FindingAid
from findingaids.fa.views import _paginate_queryset, _fa_listfields

def keyword_search(request):
    "Simple keyword search - runs exist full-text terms query on all terms included."
    # not yet implemented - if no search terms, display search form
    search_terms = request.GET.get('keywords')
    # common ead fields for list display, plus full-text relevance score
    return_fields = _fa_listfields()
    return_fields.append('fulltext_score')
    results = FindingAid.objects.filter(fulltext_terms=search_terms).order_by('fulltext_score').only(*return_fields)
    result_subset = _paginate_queryset(request, results)

    query_times = results.queryTime()
    # FIXME: does not currently include keyword param in generated urls
    # create a better browse view - display search terms, etc.

    return render_to_response('findingaids/search_results.html', 
            {'findingaids' : result_subset,
             'keywords'  : search_terms,
             'querytime': query_times})
