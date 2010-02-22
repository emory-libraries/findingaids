from django.shortcuts import render_to_response
from django.http import Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from findingaids.fa.models import FindingAid, Series, Subseries

def browse_titles(request):
    "List all first letters in finding aid list title, link to browse by letter."
    first_letters = FindingAid.objects.only(['first_letter']).order_by('list_title').distinct()
    return render_to_response('findingaids/browse_letters.html', { 'letters' : first_letters,
                                                           'xquery': first_letters.query.getQuery() })

def titles_by_letter(request, letter):
    "Paginated list of finding aids by first letter in list title"
    fa = FindingAid.objects.filter(list_title__startswith=letter).order_by('list_title').only(['eadid',
                    'list_title','title', 'author', 'unittitle', 'abstract', 'physical_desc'])
    first_letters = FindingAid.objects.only(['first_letter']).order_by('list_title').distinct()
    return _paginated_browse(request, fa, letters=first_letters, current_letter=letter)

# object pagination - adapted directly from django paginator documentation
def _paginated_browse(request, fa, letters=None, current_letter=None):
    paginator = Paginator(fa, 10)	# FIXME: should num per page be configurable?
     # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        findingaids = paginator.page(page)
    except (EmptyPage, InvalidPage):
        findingaids = paginator.page(paginator.num_pages)


    return render_to_response('findingaids/list.html', { 'findingaids' : findingaids,
                                                         'xquery': fa.query.getQuery(),
                                                         'querytime': fa.queryTime(),
                                                         'letters': letters,
                                                         'current_letter': current_letter})
    
def view_fa(request, id):
    "View a single finding aid"
    try:
        fa = FindingAid.objects.get(eadid=id)
    except Exception:       # FIXME: need queryset to raise a specific exception here?
        raise Http404
    return render_to_response('findingaids/view.html', { 'findingaid' : fa })

def view_series(request, id, series_id):
    "View a single series (c01) from a finding aid"
    try:
        series = Series.objects.also(['eadid']).get(eadid=id,id=series_id)
    except Exception:    
        raise Http404
    return render_to_response('findingaids/view_series.html', { 'series' : series })

def view_subseries(request, id, series_id, subseries_id):
    "View a single subseries (c02) from a finding aid"
#    try:
#        series = Subseries.objects.also(['eadid']).get(eadid=id,id=subseries_id)
#    except Exception:    
#        raise Http404
    series = Subseries.objects.also(['eadid']).get(eadid=id,id=subseries_id)
    return render_to_response('findingaids/view_series.html', { 'series' : series })
