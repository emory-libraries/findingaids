import datetime
from dateutil.tz import tzlocal

from django.http import HttpResponse
from django.http import Http404
from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import condition

from eulcore.django.existdb.db import ExistDB
from eulcore.existdb.exceptions import DoesNotExist # ReturnedMultiple needed also ?

from findingaids.fa.models import FindingAid, Series, Subseries, Subsubseries, title_letters, Index
from findingaids.fa.forms import KeywordSearchForm
from findingaids.fa.utils import render_to_pdf, use_preview_collection, \
            restore_publish_collection, get_findingaid, pages_to_show, \
            ead_lastmodified, ead_etag, paginate_queryset

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
    show_pages = []
    fa_subset, paginator = paginate_queryset(request, fa, per_page=10, orphans=5)
    show_pages = pages_to_show(paginator, fa_subset.number)
    query_times = [first_letters.queryTime(), fa.queryTime()]

    return render_to_response('findingaids/titles_list.html',
        {'findingaids' : fa_subset,
         'querytime': query_times,
         'letters': first_letters,
         'current_letter': letter,
         'show_pages' : show_pages},
         context_instance=RequestContext(request))

@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def view_fa(request, id, preview=False):
    "View a single finding aid"
    fa = get_findingaid(id, preview=preview)
        
    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], preview=preview)
    return render_to_response('findingaids/view.html', { 'findingaid' : fa,
                                                         'series' : series,
                                                         'all_indexes' : fa.archdesc.index,
                                                         'preview': preview},
                                            context_instance=RequestContext(request, current_app='preview'))

@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def series_or_index(request, id, series_id, preview=False):
    "View a single series (c01) or index from a finding aid"
    return _view_series(request, id, series_id, preview=preview)

@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def view_subseries(request, id, series_id, subseries_id, preview=False):
    "View a single subseries (c02) from a finding aid"   
    return _view_series(request, id, series_id, subseries_id,
                        preview=preview)

@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def view_subsubseries(request, id, series_id, subseries_id, subsubseries_id, preview=False):
    "View a single subseries (c03) from a finding aid"
    return _view_series(request, id, series_id, subseries_id, subsubseries_id,
                        preview=preview)

def _view_series(request, eadid, *series_ids, **kwargs):
    if 'preview' in kwargs and kwargs['preview']:
        use_preview_collection()
        
    # get the item to be displayed (series, subseries, index)
    result = _get_series_or_index(eadid, *series_ids)
    # info needed to construct navigation links within this ead
    # - summary info for all top-level series in this finding aid
    all_series = Series.objects.only('id', 'level', 'did__unitid', \
                            'did__unittitle').filter(ead__eadid=eadid).all()
    # - summary info for any indexes
    all_indexes = Index.objects.only('id', 'head').filter(ead__eadid=eadid).all()
    
    if 'preview' in kwargs and kwargs['preview']:
        restore_publish_collection()

    render_opts = { 'ead': result.ead,
                    'all_series' : all_series,
                    'all_indexes' : all_indexes,
                    "querytime" : [result.queryTime(), all_series.queryTime(), all_indexes.queryTime()]}
    # include any keyword args in template parameters (preview mode)
    render_opts.update(kwargs)

    if (isinstance(result, Index)):
        render_opts['index'] = result
    else:
        render_opts['series'] = result
        render_opts['subseries'] = _subseries_links(result)

    return render_to_response('findingaids/series_or_index.html',
                            render_opts, context_instance=RequestContext(request))

def _get_series_or_index(eadid, *series_ids):
    # additional fields to be returned
    return_fields = ['ead__eadid', 'ead__title', 'ead__archdesc__controlaccess__head',
        'ead__dsc__head']
    # common search parameters - last series id should be requested series, of whatever type
    search_fields = {'ead__eadid' : eadid, 'id': series_ids[-1]}
    try:
        if len(series_ids) == 1:
            try:
                record = Series.objects.also(*return_fields).get(**search_fields)
            except DoesNotExist:
                record = Index.objects.also(*return_fields).get(**search_fields)                
        elif len(series_ids) == 2:
            return_fields.append('series__id')
            search_fields["series__id"] = series_ids[0]
            record = Subseries.objects.also(*return_fields).get(**search_fields)
        elif len(series_ids) == 3:
            return_fields.extend(['series__id', 'subseries__id'])
            search_fields.update({"series__id": series_ids[0], "subseries__id" : series_ids[1]})
            record = Subsubseries.objects.also(*return_fields).get(**search_fields)
    except DoesNotExist:
        raise Http404
    return record

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
        result_subset, paginator = paginate_queryset(request, results)

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

@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def full_fa(request, id, mode, preview=False):
    "View the full contents of a single finding aid as PDF or plain html"
    fa = get_findingaid(id, preview=preview)
    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], url_callback=_series_anchor)

    template = 'findingaids/full.html'
    template_args = { 'findingaid' : fa, 'series' : series,
                    'mode' : mode, 'preview': preview, 'request' : request}
    if mode == 'html':
        return render_to_response(template, template_args)
    elif mode == 'pdf':
        return render_to_pdf(template, template_args, filename='%s.pdf' % fa.eadid)

def _fa_listfields():
    "List of fields that should be returned for brief list display of a finding aid."
    return ['eadid', 'list_title','unittitle', 'abstract', 'physical_desc']

def _series_url(eadid, series_id, *ids, **extra_opts):
    """
    Generate a series or subseries url when given an eadid and list of series ids.
    Requires at least ead document id and top-level series id.  Number of additional
    series ids provided determines type of series url generated.
    """
    # common args for generating all urls
    args = {'id' : eadid, 'series_id' : series_id}

    if len(ids) == 0:       # no additional args
        view_name = 'series-or-index'
    if len(ids) >= 1:       # add subseries id arg if one specified (used for sub and sub-subseries)
        args['subseries_id'] = ids[0]
        view_name = 'view-subseries'
    if len(ids) == 2:       # add sub-subseries id arg if specified
        args['subsubseries_id'] = ids[1]
        view_name = 'view-subsubseries'

    if 'preview' in extra_opts and extra_opts['preview'] == True:
        view_namespace = 'fa-admin:preview'
    else:
        view_namespace = 'fa'

    return reverse('%s:%s' % (view_namespace, view_name), kwargs=args)

def _series_anchor(*ids, **extra_opts):
    """Generate a same-page id-based anchor link for a series"""
    # only actually use the last of all ids passed in
    return "#%s" % ids[-1]

def _subseries_links(series, url_ids=None, url_callback=_series_url, preview=False):
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
                        % (series.node.tag, series.id))

        url_ids = [series.ead.eadid]
        # if c02/c03, check to ensure we have enough information to generate the correct link
        if series.node.tag in ['c02', 'c03']:
            # if initial series passed in is c02 or c03, add c01 series id to url ids before current series id
            if hasattr(series, 'series') and series.series:
                url_ids.append(series.series.id)
            else:
                raise Exception("Cannot construct subseries links without c01 series id for %s element %s"
                        % (series.node.tag, series.id))

            if series.node.tag == 'c03':
                # if initial series passed in is c03, add c02 series id to url ids before current series id
                if hasattr(series, 'subseries') and series.subseries:
                    url_ids.append(series.subseries.id)
                else:
                    raise Exception("Cannot construct subseries links without c02 subseries id for %s element %s"
                        % (series.node.tag, series.id))

        #  current series id
        if series.node.tag in ['c01', 'c02', 'c03']:
            url_ids.append(series.id)
        
    links = []
    if (hasattr(series, 'hasSubseries') and series.hasSubseries()) or (hasattr(series, 'hasSeries') and series.hasSeries()):
        for component in series.c:            
            current_url_ids = url_ids + [component.id]
            text = "<a href='%s'>%s</a>" % (url_callback(*current_url_ids, preview=preview), \
                            component.display_label())
            links.append(text)
            if component.hasSubseries():
                links.append(_subseries_links(component, url_ids=current_url_ids, \
                    url_callback=url_callback, preview=preview))
    return links

@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def xml_fa(request, id, preview=False):
    """
    Display the XML content of a finding aid

    :param id: the ID of an EAD
    """
    fa = get_findingaid(id, preview=preview)
    xml_ead = fa.serialize(pretty=True)
    return HttpResponse(xml_ead, mimetype='application/xml')
