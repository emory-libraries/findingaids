import logging
from urllib import urlencode

from django.http import HttpResponse, Http404, QueryDict
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import condition

from eulcore.django.http import content_negotiation
from eulcore.existdb.db import ExistDBException
from eulcore.existdb.exceptions import DoesNotExist # ReturnedMultiple needed also ?

from findingaids.fa.models import FindingAid, Series, Series2, Series3, \
            FileComponent, title_letters, Index
from findingaids.fa.forms import KeywordSearchForm, DocumentSearchForm
from findingaids.fa.utils import render_to_pdf, use_preview_collection, \
            restore_publish_collection, get_findingaid, pages_to_show, \
            ead_lastmodified, ead_etag, paginate_queryset, ead_gone_or_404, \
            collection_lastmodified, alpha_pagelabels
from findingaids.simplepages.models import SimplePage

import logging
logger = logging.getLogger(__name__);


fa_listfields = ['eadid', 'list_title','archdesc__did']
"List of fields that should be returned for brief list display of a finding aid."
# NOTE: returning archdesc/did as a single chunk instead of unittitle, abstract,
# and physdesc individually because eXist can construct the return xml much more
# efficiently; unittitle and abstract should be accessed via FindingAid.unittitle
# and FindingAid.abstract

def site_index(request):
    "Site home page.  Currently includes browse letter links."
    intro = SimplePage.objects.get(url='/intro/')   # FIXME: error handling
    return render_to_response('findingaids/index.html', {'letters': title_letters(),
                                                         'intro': intro},
                                                          context_instance=RequestContext(request)
                                                          )
def browse_titles(request):
    "List all first letters in finding aid list title, with a link to browse by letter."
    return render_to_response('findingaids/browse_letters.html',
                              {'letters': title_letters()},
                              context_instance=RequestContext(request))

# TODO: code review requested
@condition(last_modified_func=collection_lastmodified)
def titles_by_letter(request, letter):
    """Paginated list of finding aids by first letter in list title.
    Includes list of browse first-letters as in :meth:`browse_titles`.
    """
    fa = FindingAid.objects.filter(list_title__startswith=letter).order_by('list_title').only(*fa_listfields)    
    fa_subset, paginator = paginate_queryset(request, fa, per_page=10, orphans=5)
    page_labels = alpha_pagelabels(paginator, fa, label_attribute='list_title')
    show_pages = pages_to_show(paginator, fa_subset.number, page_labels)

    response_context = {
        'findingaids' : fa_subset,
         'querytime': [fa.queryTime()],
         'letters': title_letters(),
         'current_letter': letter,
         'show_pages' : show_pages,
    }
    if page_labels:     # if there is content and page labels to show, add to context
         # other page labels handled by show_pages, but first & last are special
         response_context['first_page_label'] = page_labels[1]
         response_context['last_page_label'] = page_labels[paginator.num_pages]

    return render_to_response('findingaids/titles_list.html',
        response_context, context_instance=RequestContext(request))

@ead_gone_or_404
@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def eadxml(request, id, preview=False):
    """Display the full EAD XML content of a finding aid.

    :param id: eadid for the document to be displayed
    :param preview: boolean indicating preview mode, defaults to False
    """
    fa = get_findingaid(id, preview=preview)
    xml_ead = fa.serialize(pretty=True)
    return HttpResponse(xml_ead, mimetype='application/xml')

@ead_gone_or_404
@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
@content_negotiation({'text/xml' : eadxml, 'application/xml' : eadxml})
def findingaid(request, id, preview=False):
    """View a single finding aid.   In preview mode, pulls the document from the
    configured eXist-db preview collection instead of the default public one.
    
    :param id: eadid for the document to view
    :param preview: boolean indicating preview mode, defaults to False
    """
    if 'keywords' in request.GET:
        search_terms = request.GET['keywords']
        url_params = '?' + urlencode({'keywords': search_terms})
        filter = {'highlight': search_terms}
    else:
        url_params = ''
        filter = {}
    fa = get_findingaid(id, preview=preview, filter=filter)
    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], preview=preview,
        url_params=url_params)
    return render_to_response('findingaids/findingaid.html', { 'ead' : fa,
                                                         'series' : series,
                                                         'all_indexes' : fa.archdesc.index,                                                         
                                                         'preview': preview,
                                                         'url_params': url_params,
                                                         'docsearch_form': DocumentSearchForm(),
                                                         },
                                                         context_instance=RequestContext(request, current_app='preview'))


@ead_gone_or_404
@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def full_findingaid(request, id, mode, preview=False):
    """View the full contents of a single finding aid as PDF or plain html.

    :param id: eadid for the document to be displayed
    :param mode: one of 'html' or 'pdf' - note that the html mode is not publicly
            linked anywhere, and is intended mostly for development and testing
            of the PDF display
    :param preview: boolean indicating preview mode, defaults to False
    """
    fa = get_findingaid(id, preview=preview)
    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], url_callback=_series_anchor)

    template = 'findingaids/full.html'
    template_args = { 'ead' : fa, 'series' : series,
                    'mode' : mode, 'preview': preview, 'request' : request}
    if mode == 'html':
        return render_to_response(template, template_args)
    elif mode == 'pdf':
        return render_to_pdf(template, template_args, filename='%s.pdf' % fa.eadid.value)


@condition(etag_func=ead_etag, last_modified_func=ead_lastmodified)
def series_or_index(request, id, series_id, series2_id=None,
                    series3_id=None, preview=False):
    """View a single series or subseries (c01, c02, or c03) or an index from a
    finding aid.

    :param id: eadid for the document the series belongs to
    :param series_id: c01 series or index id
    :param series2_id: c02 subseries id (optional)
    :param series3_id: c03 sub-subseries id (optional)
    :param preview: boolean indicating preview mode, defaults to False
    """
    return _view_series(request, id, series_id, series2_id, series3_id, preview=preview)

def _view_series(request, eadid, *series_ids, **kwargs):
    """Retrieve and display a series, subseries, or index.

    :param eadid: eadid for the document the series or index belongs to
    :param series_ids: list of series ids - number of ids determines series level

    Also takes an optional named argument for preview mode.
    """
    if 'preview' in kwargs and kwargs['preview']:
        use_preview_collection()

    # unspecified sub- and sub-sub-series come in as None; filter them out
    series_ids = list(series_ids)
    while None in series_ids:
        series_ids.remove(None)

    #used to build initial series and index filters and field lists
    filter_list = {'ead__eadid':eadid}
    series_fields =['id', 'level', 'did__unitid', 'did__unittitle']
    index_fields =['id', 'head']

    # info needed to construct navigation links within this ead
    # - summary info for all top-level series in this finding aid
    all_series = Series.objects.filter(**filter_list)
    # - summary info for any indexes
    all_indexes = Index.objects.filter(**filter_list)

    if 'keywords' in request.GET:
        search_terms = request.GET['keywords']
        url_params = '?' + urlencode({'keywords': search_terms})
        #filter further based on highlighting
        filter = {'highlight': search_terms}
        all_series = all_series.filter(**filter)
        all_indexes = all_indexes.filter(**filter)
        series_fields.append('match_count')
        index_fields.append('match_count')
    else:
        url_params = ''
        filter = {}
    # get the item to be displayed (series, subseries, index)
    result = _get_series_or_index(eadid, *series_ids, filter=filter)

    # info needed to construct navigation links within this ead
    # - summary info for all top-level series in this finding aid
    all_series = all_series.only(*series_fields).all()
    # - summary info for any indexes
    all_indexes = all_indexes.only(*index_fields).all()
   
    
    if 'preview' in kwargs and kwargs['preview']:
        restore_publish_collection()

    #find index of requested object so next and prev can be determined
    index = 0
    for i, s in enumerate(all_series):
        if(s.id == result.id):
            index = i
    prev= index -1
    next = index +1

    
    render_opts = { 'ead': result.ead,
                    'all_series' : all_series,
                    'all_indexes' : all_indexes,
                    "querytime" : [result.queryTime(), all_series.queryTime(), all_indexes.queryTime()],
                    'prev': prev,
                    'next': next,
                    'url_params': url_params,
                    'canonical_url' : _series_url(eadid, *series_ids),
                    'docsearch_form': DocumentSearchForm(),
                    }
    # include any keyword args in template parameters (preview mode)
    render_opts.update(kwargs)

    if (isinstance(result, Index)):
        render_opts['index'] = result
    else:
        render_opts['series'] = result
        render_opts['subseries'] = _subseries_links(result, url_params=url_params)

    return render_to_response('findingaids/series_or_index.html',
                            render_opts, context_instance=RequestContext(request))

def _get_series_or_index(eadid, *series_ids, **kwargs):
    """Retrieve a series or index from a Finding Aid.

    :param eadid: eadid for the document the series or index belongs to
    :param series_ids: list of series ids or an index id; for series,
            the number of ids determines series level to be retrieved
    """
    # additional fields to be returned
    return_fields = ['ead__eadid', 'ead__title', 'ead__archdesc__controlaccess__head',
        'ead__dsc__head']
    # common search parameters - last series id should be requested series, of whatever type
    search_fields = {'ead__eadid' : eadid, 'id': series_ids[-1]}

    if 'filter' in kwargs:
        filter = kwargs['filter']
    try:
        if len(series_ids) == 1:
            # if there is only on id, either a series or index is requested
            try:
                # try to find a series first (more common)
                queryset = Series.objects.also(*return_fields).filter(**search_fields)
                if filter:
                    queryset = queryset.filter(**filter)
                record = queryset.get()
            except DoesNotExist:
                # if series is not found, look for an index
                queryset = Index.objects.also(*return_fields).filter(**search_fields)
                if filter:
                    queryset = queryset.filter(**filter)
                record = queryset.get()                
            return record
        
        elif len(series_ids) == 2:
            return_fields.append('series__id')
            search_fields["series__id"] = series_ids[0]
            queryset = Series2.objects
        elif len(series_ids) == 3:
            return_fields.extend(['series__id', 'series2__id'])
            search_fields.update({"series__id": series_ids[0], "series2__id" : series_ids[1]})
            queryset = Series3.objects
        
        queryset = queryset.filter(**search_fields).also(*return_fields)
        # if there are any additional filters specified, apply before getting item
        # NOTE: applying search fields filter first because it should be faster (find by id)
        if filter:
            queryset = queryset.filter(**filter)
        record = queryset.get()
        
    except DoesNotExist:
        raise Http404
    return record

def keyword_search(request):
    "Simple keyword search - runs exist full-text terms query on all terms included."
    
    tips = SimplePage.objects.get(url='/search/')   # FIXME: error handling ?
    form = KeywordSearchForm(request.GET)
    query_error = False
    
    if form.is_valid():
        search_terms = form.cleaned_data['keywords']
        # common ead fields for list display, plus full-text relevance score
        return_fields = fa_listfields[:]     # copy! don't modify master list
        return_fields.append('fulltext_score')
        try:
            results = FindingAid.objects.filter(
                    # first do a full-text search to restrict to relevant documents
                    fulltext_terms=search_terms
                ).or_filter(
                    # do an OR search on boosted fields, so that relevance score
                    # will be calculated based on boosted field values
                    fulltext_terms=search_terms,
                    boostfields__fulltext_terms=search_terms,
                    highlight=False,    # disable highlighting in search results list
                ).order_by('-fulltext_score').only(*return_fields)
            result_subset, paginator = paginate_queryset(request, results, per_page=10, orphans=5)
            show_pages = pages_to_show(paginator, result_subset.number)

            query_times = results.queryTime()
            # FIXME: does not currently include keyword param in generated urls
            # create a better browse view - display search terms, etc.
            
            #build query string to pass to pass additional arguments in query string (currently only keywords)
            query_params = {
            'keywords':search_terms,
            }

            query_string = QueryDict('')
            query_string = query_string.copy()
            query_string.update(query_params)
            query_string = query_string.urlencode()

            return render_to_response('findingaids/search_results.html',
                    {'findingaids' : result_subset,
                     'keywords'  : search_terms,
                     #TODO combine url_params and query_string
                     'url_params' : '?' + urlencode({'keywords': search_terms}),
                     'querytime': [query_times],
                     'show_pages' : show_pages,
                     'query_string':query_string},
                     context_instance=RequestContext(request))
        except ExistDBException, e:
            # for an invalid full-text query (e.g., missing close quote), eXist
            # error reports 'Cannot parse' and 'Lexical error'
            # FIXME: could/should this be a custom eXist exception class?
            query_error = True
            if 'Cannot parse' in e.message():
                messages.error(request,
                    'Your search query could not be parsed.  Please revise your search and try again.')
            else:
                # generic error message for any other exception
                messages.error(request, 'There was an error processing your search.')
    else:
        # if form was not valid, re-initialize
        # don't tell the user the field is required if they haven't submitted anything!
        form = KeywordSearchForm()

    # if form is invalid (no search terms) or there was an error, display search form
    response = render_to_response('findingaids/search_form.html',
                    {'form' : form, 'request': request, 'tips': tips },
                    context_instance=RequestContext(request))
    # if query could not be parsed, set a 'Bad Request' status code on the response
    if query_error:
        response.status_code = 400
    return response

def document_search(request, id):
    "Keyword search on file-level items in a single Finding Aid."

    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        search_terms = form.cleaned_data['keywords']
        files = FileComponent.objects.filter(ead__eadid=id,
            fulltext_terms=search_terms).also('series__id', 'series__did')

        query_times = files.queryTime()
        ead = get_findingaid(id, only=['eadid', 'title'])

        return render_to_response('findingaids/document_search.html', {
                'files' : files,
                'ead': ead,
                'querytime': [query_times],
             }, context_instance=RequestContext(request))
    # TODO: error handling, invalid form, etc.

def _series_url(eadid, series_id, *ids, **extra_opts):
    """
    Generate a series or subseries url when given an eadid and list of series ids.
    Requires at least ead document id and top-level series id.  Number of additional
    series ids provided determines type of series url generated.

    Default url callback for :meth:`_subseries_links`.
    """
    # common args for generating all urls
    args = {'id' : eadid, 'series_id' : series_id}

    if len(ids) == 0:       # no additional args
        view_name = 'series-or-index'
    if len(ids) >= 1:       # add subseries id arg if one specified (used for sub and sub-subseries)
        args['series2_id'] = ids[0]
        view_name = 'series2'
    if len(ids) == 2:       # add sub-subseries id arg if specified
        args['series3_id'] = ids[1]
        view_name = 'series3'

    if 'preview' in extra_opts and extra_opts['preview'] == True:
        view_namespace = 'fa-admin:preview'
    else:
        view_namespace = 'fa'

    return reverse('%s:%s' % (view_namespace, view_name), kwargs=args)

def _series_anchor(*ids, **extra_opts):
    """Generate a same-page id-based anchor link for a series.

    Used as url callback for :meth:`_subseries_links` for generating a single-page
    version of the full finding aid (see :meth:`full_fa`).
    """
    # only actually use the last of all ids passed in
    return "#%s" % ids[-1]

def _subseries_links(series, url_ids=None, url_callback=_series_url, preview=False,
        url_params=''):
    """
    Recursive function to build a nested list of links to series and subseries
    to simplify template display logic for complicated series.  Note that the list
    elements include ``<a href="...">`` tags, so the output of should not be
    escaped in the template where it is rendered.

    Series element must include ead.eadid; if series is c02 or c03, must also
    include parent c01 (and c02) id, in order to generate urls.

    :param series: :class:`findingaids.fa.models.Series` instance (with access 
            to eadid for the document and parent series ids if a subseries)
    :param url_ids: list of series ids for generating urls
    :param url_callback: method to use for generating the series url
    :param preview: boolean; when True, links will be generated for preview urls.
            Optional, defaults to False.
    :param url_params: optional string to add to the end of urls (e.g., for search
            term highlighting)
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
                if hasattr(series, 'series2') and series.series2:
                    url_ids.append(series.series2.id)
                else:
                    raise Exception("Cannot construct subseries links without c02 subseries id for %s element %s"
                        % (series.node.tag, series.id))

        #  current series id
        if series.node.tag in ['c01', 'c02', 'c03']:
            url_ids.append(series.id)
        
    links = []
    if (hasattr(series, 'hasSubseries') and series.hasSubseries()) or (hasattr(series, 'hasSeries') and series.hasSeries()):
        for component in series.c:
            # get match count for each series / subseries and append it to the link if > 0
            if component.match_count > 0:
                plural ="es" if component.match_count > 1 else ""
                match_count = "<span class='exist-match'>%s match%s</span>" %(component.match_count, plural)
            else:
                match_count = ""

            current_url_ids = url_ids + [component.id]
            #set c01 rel attrib to 'section' c02 and c03 to 'subsection'
            if (component.node.tag == 'c01'):
                rel='section'
            elif (component.node.tag in ['c02', 'c03']):
                rel='subsection'
            text = "<a href='%(url)s%(url_params)s' rel='%(rel)s'>%(linktext)s</a> %(match_count)s" % \
                {'url': url_callback(*current_url_ids, preview=preview),
                 'url_params': url_params,
                 'rel': rel,
                 'linktext':  component.display_label(), 'match_count': match_count}
            links.append(text)
            if component.hasSubseries():
                links.append(_subseries_links(component, url_ids=current_url_ids, \
                    url_callback=url_callback, preview=preview, url_params=url_params))
    return links
