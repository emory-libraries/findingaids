from django.shortcuts import render_to_response
from django.http import Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.template import RequestContext
from findingaids.fa.models import FindingAid, Series, Subseries, Subsubseries, title_letters, Index
from findingaids.fa.forms import KeywordSearchForm
from findingaids.fa.utils import render_to_pdf

def site_index(request):
    "Site home page"
    first_letters = title_letters()
    return render_to_response('findingaids/index.html', { 'letters' : first_letters,
                                                          'querytime': [first_letters.queryTime()]},
                                                          context_instance=RequestContext(request)
                                                          )

def browse_titles(request):
    "List all first letters in finding aid list title, link to browse by letter."
    first_letters = title_letters()
    return render_to_response('findingaids/browse_letters.html', { 'letters' : first_letters,
                                                           'querytime': [first_letters.queryTime()]},
                                                          context_instance=RequestContext(request))

def titles_by_letter(request, letter):
    "Paginated list of finding aids by first letter in list title"
    first_letters = title_letters()

    fa = FindingAid.objects.filter(list_title__startswith=letter).order_by('list_title').only(*_fa_listfields())   
    fa_subset = _paginate_queryset(request, fa)
    query_times = [first_letters.queryTime(), fa.queryTime()]

    return render_to_response('findingaids/titles_list.html',
        {'findingaids' : fa_subset,
         'querytime': query_times,
         'letters': first_letters,
         'current_letter': letter},
         context_instance=RequestContext(request))

# object pagination - adapted directly from django paginator documentation
def _paginate_queryset(request, qs, per_page=10):
    # FIXME: should num-per-page be configurable via local settings?
    paginator = Paginator(qs, per_page)
     # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        paginated_qs = paginator.page(page)
    except (EmptyPage, InvalidPage):
        paginated_qs = paginator.page(paginator.num_pages)

    return paginated_qs


def view_fa(request, id):
    "View a single finding aid"
    try:
        fa = FindingAid.objects.get(eadid=id)
    except Exception:       # FIXME: need queryset to raise a specific exception here?
        raise Http404

    series = _subseries_links(fa.dsc, url_ids=[fa.eadid])
    
    return render_to_response('findingaids/view.html', { 'findingaid' : fa,
                                                         'series' : series},
                                                         context_instance=RequestContext(request))

def view_series(request, id, series_id):
    "View a single series (c01) from a finding aid"
    return _view_series(request, id, series_id)

def view_subseries(request, id, series_id, subseries_id):
    "View a single subseries (c02) from a finding aid"   
    return _view_series(request, id, series_id, subseries_id)

def view_subsubseries(request, id, series_id, subseries_id, subsubseries_id):
    "View a single subseries (c03) from a finding aid"
    return _view_series(request, id, series_id, subseries_id, subsubseries_id)


def _view_series(request, eadid, *series_ids):
    # additional fields to be returned
    return_fields = ['ead__eadid', 'ead__title', 'ead__archdesc__controlaccess__head',
        'ead__dsc__head']
        # NOTE: partial result can't handle list fields properly; retreiving index list separately
    # common search parameters - last series id should be requested series, of whatever type
    search_fields = {'ead__eadid' : eadid, 'id': series_ids[-1]}
    try:
        if len(series_ids) == 1:
            series = Series.objects.also(*return_fields).get(**search_fields)
        elif len(series_ids) == 2:
            return_fields.append('series__id')
            search_fields["series__id"] = series_ids[0]
            series = Subseries.objects.also(*return_fields).get(**search_fields)
        elif len(series_ids) == 3:
            return_fields.extend(['series__id', 'subseries__id'])
            search_fields.update({"series__id": series_ids[0], "subseries__id" : series_ids[1]})
            series = Subsubseries.objects.also(*return_fields).get(**search_fields)
    except Exception:       # FIXME: limit to a more specific exception here...
        raise Http404
            
    # summary info for all top-level series in this finding aid
    all_series = Series.objects.only('id', 'level', 'did__unitid', 'did__unittitle').filter(ead__eadid=eadid).all()
    # summary info for any indexes
    all_indexes = Index.objects.only('id', 'head').filter(ead__eadid=eadid).all()
    return render_to_response('findingaids/view_series.html', { 'series' : series,
                                                                'all_series' : all_series,
                                                                'all_indexes' : all_indexes,
                                                                "subseries" : _subseries_links(series),
                                                                # anyway to get query time for series object?
                                                                "querytime" : [series.queryTime(), all_series.queryTime(), all_indexes.queryTime()]},
                                                                context_instance=RequestContext(request))



def keyword_search(request):
    "Simple keyword search - runs exist full-text terms query on all terms included."
    form = KeywordSearchForm(request.GET)
    if form.is_valid():
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
                 'querytime': [query_times]},
                 context_instance=RequestContext(request))
    else:
        form = KeywordSearchForm()
            
    return render_to_response('findingaids/search_form.html',
                    {'form' : form, 'request': request },
                    context_instance=RequestContext(request))

def full_fa(request, id, mode):
    "View the full contents of a single finding aid as PDF or plain html"
    try:
        fa = FindingAid.objects.get(eadid=id)
    except Exception:       # FIXME: need queryset to raise a specific exception here?
        raise Http404

    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], url_callback=_series_anchor)

    template = 'findingaids/full.html'
    template_args = { 'findingaid' : fa, 'series' : series,
                    'mode' : mode, 'request' : request}
    if mode == 'html':
        return render_to_response(template, template_args)
    elif mode == 'pdf':
        return render_to_pdf(template, template_args, filename='%s.pdf' % fa.eadid)

def _fa_listfields():
    "List of fields that should be returned for brief list display of a finding aid."
    return ['eadid', 'list_title','title', 'abstract', 'physical_desc']

def _series_url(eadid, series_id, *ids):
    """
    Generate a series or subseries url when given an eadid and list of series ids.
    Requires at least ead document id and top-level series id.  Number of additional
    series ids provided determines type of series url generated.
    """
    # common args for generating all urls
    args = {'id' : eadid, 'series_id' : series_id}

    if len(ids) == 0:       # no additional args
        urlname = 'fa:view-series'
    if len(ids) >= 1:       # add subseries id arg if one specified (used for sub and sub-subseries)
        args['subseries_id'] = ids[0]
        urlname = 'fa:view-subseries'
    if len(ids) == 2:       # add sub-subseries id arg if specified
        args['subsubseries_id'] = ids[1]
        urlname = 'fa:view-subsubseries'

    return reverse(urlname, kwargs=args)

def _series_anchor(*ids):
    """Generate a same-page id-based anchor link for a series"""
    # only actually use the last of all ids passed in
    return "#%s" % ids[-1]

def _subseries_links(series, url_ids=None, url_callback=_series_url):
    """
    Recursive function to build a nested list of links to series and subseries
    to simplify template display logic for complicated series.

    Series element must include ead.eadid; if series is c02 or c03, must also
    include parent c01 (and c02) id, in order to generate urls.
    """
    # construct url ids if none are passed
    if url_ids is None:
        if not (series.ead and series.ead.eadid):
            raise Exception("Cannot construct subseries links without eadid for %s element %s"
                        % (series.dom_node.nodeName, series.id))

        url_ids = [series.ead.eadid]
        # if c02/c03, check to ensure we have enough information to generate the correct link
        if series.dom_node.nodeName in ['c02', 'c03']:
            # if initial series passed in is c02 or c03, add c01 series id to url ids before current series id
            if hasattr(series, 'series') and series.series:
                url_ids.append(series.series.id)
            else:
                raise Exception("Cannot construct subseries links without c01 series id for %s element %s"
                        % (series.dom_node.nodeName, series.id))

            if series.dom_node.nodeName == 'c03':
                # if initial series passed in is c03, add c02 series id to url ids before current series id
                if hasattr(series, 'subseries') and series.subseries:
                    url_ids.append(series.subseries.id)
                else:
                    raise Exception("Cannot construct subseries links without c02 subseries id for %s element %s"
                        % (series.dom_node.nodeName, series.id))

        #  current series id
        if series.dom_node.nodeName in ['c01', 'c02', 'c03']:
            url_ids.append(series.id)
        
    links = []
    if (hasattr(series, 'hasSubseries') and series.hasSubseries()) or (hasattr(series, 'hasSeries') and series.hasSeries()):
        for component in series.c:            
            current_url_ids = url_ids + [component.id]
            text = "<a href='%s'>%s</a>" % (apply(url_callback, current_url_ids), component.display_label())
            links.append(text)
            if component.hasSubseries():
                links.append(_subseries_links(component, url_ids=current_url_ids, url_callback=url_callback))
    return links
