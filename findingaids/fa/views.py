# file findingaids/fa/views.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
from lxml import etree
from urllib import urlencode

from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import condition

from eulcommon.djangoextras.http import content_negotiation
from eulexistdb.db import ExistDBException, ExistDBTimeout
from eulexistdb.exceptions import DoesNotExist  # ReturnedMultiple needed also ?
from eulxml.xmlmap.eadmap import EAD_NAMESPACE

from findingaids.fa.models import FindingAid, Series, Series2, Series3, \
    FileComponent, title_letters, Index, shortform_id
from findingaids.fa.forms import KeywordSearchForm, AdvancedSearchForm
from findingaids.fa.utils import render_to_pdf, get_findingaid, pages_to_show, \
    ead_lastmodified, ead_etag, paginate_queryset, ead_gone_or_404, \
    collection_lastmodified, alpha_pagelabels, html_to_xslfo

logger = logging.getLogger(__name__)


fa_listfields = ['eadid', 'list_title', 'archdesc__did']
"List of fields that should be returned for brief list display of a finding aid."
# NOTE: returning archdesc/did as a single chunk instead of unittitle, abstract,
# and physdesc individually because eXist can construct the return xml much more
# efficiently; unittitle and abstract should be accessed via FindingAid.unittitle
# and FindingAid.abstract


RDFA_NAMESPACES = {
    'schema': 'http://schema.org/',
    'dcmitype': 'http://purl.org/dc/dcmitype/',
    'arch': 'http://purl.org/archival/vocab/arch#',
    'bibo': 'http://purl.org/ontology/bibo/',
}


def site_index(request):
    "Site home page.  Currently includes browse letter links."
    return render_to_response('fa/index.html', {'letters': title_letters()},
                              context_instance=RequestContext(request))


def browse_titles(request):
    "List all first letters in finding aid list title, with a link to browse by letter."
    return render_to_response('fa/browse_letters.html',
                              {'letters': title_letters()},
                              context_instance=RequestContext(request))


@condition(last_modified_func=collection_lastmodified)
def titles_by_letter(request, letter):
    """Paginated list of finding aids by first letter in list title.
    Includes list of browse first-letters as in :meth:`browse_titles`.
    """

    # set last browse letter and page in session
    page = request.REQUEST.get('page', 1)
    last_search = "%s?page=%s" % (reverse("fa:titles-by-letter", kwargs={'letter': letter}), page)
    last_search = {"url": last_search, "txt": "Return to Browse Results"}
    request.session['last_search'] = last_search
    request.session.set_expiry(0)  # set to expire when browser closes

    # using ~ to do case-insensitive ordering
    fa = FindingAid.objects.filter(list_title__startswith=letter).order_by('~list_title').only(*fa_listfields)
    fa_subset, paginator = paginate_queryset(request, fa, per_page=10, orphans=5)
    page_labels = alpha_pagelabels(paginator, fa, label_attribute='list_title')
    # No longer restricting the number of page labels shown using pages_to_show (like we do for numeric pages).
    # That doesn't make sense here, since the alpha range labels should ideally allow anyone to jump directly
    # to the section they want based on the labels.

    response_context = {
        'findingaids': fa_subset,
        'querytime': [fa.queryTime()],
        'letters': title_letters(),
        'current_letter': letter,
        'show_pages': page_labels,
    }
    if page_labels:
        response_context['title_range'] = page_labels[fa_subset.number]
         # current page range label is displayed in the title bar of the browser to indicate which page you are on
         #example: (Cua - Cut)

    # no special first/last page label is required, since we are displaying all labels (not limiting to 9)

    return render_to_response('fa/titles_list.html',
                              response_context,
                              context_instance=RequestContext(request))


@condition(last_modified_func=collection_lastmodified)
def xml_titles(request):
    """List all findingaids in the database and link to the EAD xml,
    as a simple way to make content available for harvesting.
    """
    # retrieve  all findingaids in the database and return eadids
    # - no sorting, title, etc. - barebones display for
    fa = FindingAid.objects.only('eadid')
    response_context = {
        'findingaids': fa,
    }

    return render_to_response('fa/xml.html',
                              response_context,
                              context_instance=RequestContext(request))


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
@content_negotiation({'text/xml': eadxml, 'application/xml': eadxml})
def findingaid(request, id, preview=False):
    """View a single finding aid.   In preview mode, pulls the document from the
    configured eXist-db preview collection instead of the default public one.

    :param id: eadid for the document to view
    :param preview: boolean indicating preview mode, defaults to False
    """
    if 'keywords' in request.GET:
        search_terms = request.GET['keywords']
        url_params = '?' + urlencode({'keywords': search_terms.encode('utf-8')})
        filter = {'highlight': search_terms}
    else:
        url_params = ''
        filter = {}
    fa = get_findingaid(id, preview=preview, filter=filter)
    last_modified = ead_lastmodified(request, id, preview)
    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], preview=preview,
                              url_params=url_params)

    extra_ns = RDFA_NAMESPACES.copy()
    # add any non-default namespaces from the EAD document
    extra_ns.update(dict((prefix, ns) for prefix, ns in fa.node.nsmap.iteritems()
                    if prefix is not None))
    context = {
        'ead': fa,
        'series': series,
        'all_indexes': fa.archdesc.index,
        'preview': preview,
        'url_params': url_params,
        'docsearch_form': KeywordSearchForm(),
        'last_search': request.session.get('last_search', None),
        'feedback_opts': _get_feedback_options(request, id),
        'extra_ns': extra_ns,
        'last_modified': last_modified,
    }

    # provide series list without keyword params to use in RDFa uris
    if url_params and not preview:
        context['series_noparam'] = _subseries_links(fa.dsc, url_ids=[fa.eadid])

    response = render_to_response('fa/findingaid.html', context,
        context_instance=RequestContext(request, current_app='preview'))
    # Set Cache-Control to private when there is a last_search
    if "last_search" in request.session:
        response['Cache-Control'] = 'private'

    return response


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
    series = _subseries_links(fa.dsc, url_ids=[fa.eadid], url_callback=_series_anchor, preview=preview)

    template = 'fa/full.html'
    template_args = {'ead': fa, 'series': series,
                     'mode': mode, 'preview': preview, 'request': request,
                     # normally supplied by context processor
                     'DEFAULT_DAO_LINK_TEXT': getattr(settings, 'DEFAULT_DAO_LINK_TEXT',
                                                      '[Resource available online]')
                     }
    if mode == 'html':
        return render_to_response(template, template_args)
    elif mode == 'pdf':
        return render_to_pdf(template, template_args, filename='%s.pdf' % fa.eadid.value)
    elif mode == 'xsl-fo':
        xslfo = html_to_xslfo(template, template_args)
        return HttpResponse(etree.tostring(xslfo), mimetype='application/xml')


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
    # explicitly set the collection to be queried so we can always use it, whether in preview mode or not
    collection = settings.EXISTDB_ROOT_COLLECTION
    if 'preview' in kwargs and kwargs['preview']:
        collection = settings.EXISTDB_PREVIEW_COLLECTION
        preview_mode = True
    else:
        preview_mode = False

    # unspecified sub- and sub-sub-series come in as None; filter them out
    _series_ids = list(series_ids)
    while None in _series_ids:
        _series_ids.remove(None)

    # user-facing urls should use short-form ids (eadid not repeated)
    # to query eXist, we need full ids with eadid
    # check and convert them here
    series_ids = []
    redirect_ids = []
    redirect = False
    for id in _series_ids:
        if id.startswith('%s_' % eadid):
            # an unshortened id was passed in - shorten and redirect to canonical url
            redirect = True
            redirect_ids.append(shortform_id(id, eadid))
        else:
            # a shortened id was passed in - generate long-form for query to exist
            series_ids.append('%s_%s' % (eadid, id))
            # append to redirect ids in case redirect is required for a later id
            redirect_ids.append(id)

    # if any id was passed in unshortened, return a permanent redirect to the canonical url
    if redirect:
        # log redirects - if any of them are coming from this application, they should be fixed
        if 'HTTP_REFERER' in request.META:
            referrer = 'Referrer %s' % request.META['HTTP_REFERER']
        else:
            referrer = ' (referrer not available)'

        logger.info('''Redirecting from long-form series/index %s url to short-form url. %s'''
                    % (request.path, referrer))
        return HttpResponsePermanentRedirect(_series_url(eadid, *redirect_ids))

    # build initial series and index filters and field lists
    filter_list = {'ead__eadid': eadid}
    series_fields = ['id', 'level', 'did__unitid', 'did__unittitle']
    index_fields = ['id', 'head']

    # info needed to construct navigation links within this ead
    # - summary info for all top-level series in this finding aid
    all_series = Series.objects.filter(**filter_list).using(collection)
    # - summary info for any indexes
    all_indexes = Index.objects.filter(**filter_list).using(collection)

    if 'keywords' in request.GET:
        search_terms = request.GET['keywords']
        url_params = '?' + urlencode({'keywords': search_terms.encode('utf-8')})
        #filter further based on highlighting
        filter = {'highlight': search_terms}
        # add highlighting & match counts to series & index lists for navigation links
        all_series = all_series.filter(**filter)
        all_indexes = all_indexes.filter(**filter)
        series_fields.append('match_count')
        index_fields.append('match_count')

    else:
        url_params = ''
        filter = {}
    # get the item to be displayed (series, subseries, index)
    result = _get_series_or_index(eadid, *series_ids, filter=filter, use_collection=collection)

    if 'keywords' in request.GET:
        # when full-text highlighting is enabled, ead must be retrieved separately
        # in order to retrieve match counts for main page ToC items

        # fields needed for top-level display (some redundancy with list in _get_series_or_index)
        return_fields = ['eadid', 'title', 'archdesc__controlaccess__head',
                         'archdesc__origination',
                         'dsc__head', 'archdesc__did']
        fa = FindingAid.objects.filter(eadid=eadid).filter(**filter).using(collection)
        # using raw xpaths for exist-specific logic to expand and count matches
        ead = fa.only(*return_fields) \
                .only_raw(coll_desc_matches=FindingAid.coll_desc_matches_xpath,
                          admin_info_matches=FindingAid.admin_info_matches_xpath,
                          archdesc__controlaccess__match_count=FindingAid.controlaccess_matches_xpath) \
                .using(collection).get()
    else:
        # when no highlighting, use partial ead retrieved with main item
        ead = result.ead

    # info needed to construct navigation links within this ead
    # - summary info for all top-level series in this finding aid
    all_series = all_series.only(*series_fields).all()
    # - summary info for any indexes
    all_indexes = all_indexes.only(*index_fields).all()

    #find index of requested object so next and prev can be determined
    index = 0
    for i, s in enumerate(all_series):
        if(s.id == result.id):
            index = i
    prev = index - 1
    next = index + 1

    query_times = [result.queryTime(), all_series.queryTime(), all_indexes.queryTime()]
    if hasattr(ead, 'queryTime'):
        query_times.append(ead.queryTime())

    extra_ns = RDFA_NAMESPACES.copy()
    # add any non-default namespaces from the EAD document
    extra_ns.update(dict((prefix, ns) for prefix, ns in ead.node.nsmap.iteritems()
                    if prefix is not None))

    render_opts = {
        'ead': ead,
        'all_series': all_series,
        'all_indexes': all_indexes,
        'querytime': query_times,
        'prev': prev,
        'next': next,
        'url_params': url_params,
        'canonical_url': _series_url(eadid, *[shortform_id(id) for id in series_ids]),
        'docsearch_form': KeywordSearchForm(),
        'last_search': request.session.get('last_search', None),
        'feedback_opts': _get_feedback_options(request, eadid),
        'extra_ns': extra_ns,
        'last_modified': ead_lastmodified(request, eadid, preview_mode)
    }
    # include any keyword args in template parameters (preview mode)
    render_opts.update(kwargs)

    if (isinstance(result, Index)):
        render_opts['index'] = result
    else:
        render_opts['series'] = result
        render_opts['subseries'] = _subseries_links(result, preview=preview_mode, url_params=url_params)

        # provide series list without keyword params to use in RDFa uris
        if url_params and not preview_mode:
            render_opts['subseries_noparam'] = _subseries_links(result)


    response = render_to_response('fa/series_or_index.html',
                                  render_opts,
                                  context_instance=RequestContext(request))

    #Cache-Control to private when there is a last_search
    if "last_search" in request.session:
        response['Cache-Control'] = 'private'

    return response


def _get_series_or_index(eadid, *series_ids, **kwargs):
    """Retrieve a series or index from a Finding Aid.

    :param eadid: eadid for the document the series or index belongs to
    :param series_ids: list of series ids or an index id; for series,
            the number of ids determines series level to be retrieved
    """
    # additional fields to be returned
    return_fields = ['ead__eadid', 'ead__title', 'ead__unittitle',
                     'ead__archdesc__origination',
                     'ead__archdesc__controlaccess__head', 'ead__dsc__head',
                     'ead__origination_name',
                     'ead__collection_id']
    # common search parameters - last series id should be requested series, of whatever type
    search_fields = {'ead__eadid': eadid, 'id': series_ids[-1]}

    filter = None
    if 'filter' in kwargs:
        filter = kwargs['filter']
    use_collection = None
    if 'use_collection' in kwargs:
        use_collection = kwargs['use_collection']

    try:
        if len(series_ids) == 1:
            # if there is only on id, either a series or index is requested
            try:
                # try to find a series first (more common)
                queryset = Series.objects.also(*return_fields).filter(**search_fields)
                if filter:
                    queryset = queryset.filter(**filter)
                if use_collection is not None:
                    queryset = queryset.using(use_collection)
                record = queryset.get()
            except DoesNotExist:
                # if series is not found, look for an index
                queryset = Index.objects.also(*return_fields).filter(**search_fields)
                if filter:
                    queryset = queryset.filter(**filter)
                if use_collection is not None:
                    queryset = queryset.using(use_collection)
                record = queryset.get()
            return record

        elif len(series_ids) == 2:
            # returning a subseries (c02); include id and did from parent c01 for breadcrumbs
            return_fields.extend(['series__id', 'series__did'])
            search_fields["series__id"] = series_ids[0]
            queryset = Series2.objects
        elif len(series_ids) == 3:
            # returning a sub-subseries (c03); include ids and dids from c01 and c02
            # series this c03 belogs to, for generating breadcrumbs
            return_fields.extend(['series__id', 'series2__id', 'series__did', 'series2__did'])
            search_fields.update({"series__id": series_ids[0], "series2__id": series_ids[1]})
            queryset = Series3.objects

        # search by the most specific filter first (direct id) to make eXist xquery as efficient as possible
        other_filters = search_fields.copy()
        del other_filters['id']
        queryset = queryset.filter(id=search_fields['id']).filter(**other_filters).also(*return_fields)
        # if there are any additional filters specified, apply before getting item
        # NOTE: applying search fields filter first because it should be faster (find by id)
        if filter:
            queryset = queryset.filter(**filter)
        if use_collection is not None:
            queryset = queryset.using(use_collection)
        record = queryset.get()

    except DoesNotExist:
        raise Http404
    return record


def _get_feedback_options(request, id):
    'Generate single-finding aid feedback options as a url parameter.'
    return urlencode({'eadid': id, 'url': request.build_absolute_uri()})


@condition(last_modified_func=collection_lastmodified)
def search(request):
    "Simple keyword search - runs exist full-text terms query on all terms included."

    form = AdvancedSearchForm(request.GET)
    query_error = False

    if form.is_valid():
        # form validation requires that at least one of subject & keyword is not empty
        subject = form.cleaned_data['subject']
        keywords = form.cleaned_data['keywords']
        repository = form.cleaned_data['repository']
        dao = form.cleaned_data['dao']
        page = request.REQUEST.get('page', 1)

        # initialize findingaid queryset - filters will be added based on search terms
        findingaids = FindingAid.objects

        # local copy of return fields (fulltext-score may be added-- don't modify master copy!)
        return_fields = fa_listfields[:]

        try:
            if subject:
                # if a subject was specified, filter on subject
                findingaids = findingaids.filter(subject__fulltext_terms=subject).order_by('list_title')
                # order by list title when searching by subject only
                # (if keywords are specified, fulltext score ordering will override this)
            if repository:
                # if repository is set, filter finding aids by requested repository
                # expecting repository value to come in as exact phrase
                findingaids = findingaids.filter(repository__fulltext_terms=repository).order_by('list_title')
            if keywords:
                # if keywords were specified, do a fulltext search
                return_fields.append('fulltext_score')
                findingaids = findingaids.filter(
                    # first do a full-text search to restrict to relevant documents
                    fulltext_terms=keywords
                ).or_filter(
                    # do an OR search on boosted fields, so that relevance score
                    # will be calculated based on boosted field values
                    fulltext_terms=keywords,
                    boostfields__fulltext_terms=keywords,
                    highlight=False,    # disable highlighting in search results list
                ).order_by('-fulltext_score')

            # optional filter: restrict to items with digital archival objects
            if dao:
                findingaids = findingaids.filter(daos__exists=True)

                # if user does not have permission to view internal daos,
                # restrict to public daos only
                if not request.user.has_perm('fa_admin.can_view_internal_dao'):
                    findingaids = findingaids.filter(public_dao_count__gte=1)

                # NOTE: using >= filter to force a where clause because this works
                # when what seems to be the same filter on the xpath does not
                # (possibly an indexing issue?)

            findingaids = findingaids.only(*return_fields)
            result_subset, paginator = paginate_queryset(request, findingaids,
                                                         per_page=10, orphans=5)
            # when searching by subject only, use alpha pagination
            if subject and not keywords:
                page_labels = alpha_pagelabels(paginator, findingaids,
                                               label_attribute='list_title')
            else:
                page_labels = {}
            show_pages = pages_to_show(paginator, result_subset.number, page_labels)
            query_times = findingaids.queryTime()

            # select non-empty form values for use in template
            search_params = dict((key, value) for key, value in form.cleaned_data.iteritems()
                                 if value)

            # set query and last page in session and set it to expire on browser close
            for key, val in search_params.iteritems():
                if key == 'dao':
                    search_params[key] = val
                else:
                    search_params[key] = val.encode('utf-8')
            last_search = search_params.copy()
            # pagination url params should NOT include page
            if 'page' in last_search:
                del(last_search['page'])
            url_params = urlencode(last_search)

            # store the current page (even if not specified in URL) for saved search
            last_search['page'] = page
            last_search = "%s?%s" % (reverse("fa:search"), urlencode(last_search))
            last_search = {"url": last_search, "txt": "Return to Search Results"}
            request.session["last_search"] = last_search
            request.session.set_expiry(0)  # set to expire when browser closes

            # ONLY keywords - not page or subject - should be included in
            # document url for search term highlighting
            if 'keywords' in search_params:
                highlight_params = urlencode({'keywords': search_params['keywords']})
            else:
                highlight_params = None

            response_context = {
                'findingaids': result_subset,
                'search_params': search_params,    # actual search terms, for display
                'url_params': url_params,   # url opts for pagination
                'highlight_params': highlight_params,  # keyword highlighting
                'querytime': [query_times],
                'show_pages': show_pages
            }
            if page_labels:     # if there are page labels to show, add to context
                # other page labels handled by show_pages, but first & last are special
                response_context['first_page_label'] = page_labels[1]
                response_context['last_page_label'] = page_labels[paginator.num_pages]

            return render_to_response('fa/search_results.html',
                                      response_context,
                                      context_instance=RequestContext(request))

        except ExistDBException, e:
            # for an invalid full-text query (e.g., missing close quote), eXist
            # error reports 'Cannot parse' and 'Lexical error'
            # FIXME: could/should this be a custom eXist exception class?
            query_error = True
            if 'Cannot parse' in e.message():
                messages.error(request,
                               'Your search query could not be parsed.  ' +
                               'Please revise your search and try again.')
            else:
                # generic error message for any other exception
                messages.error(request, 'There was an error processing your search.')
    elif 'keywords' not in request.GET and 'subject' not in request.GET:
        # if form was not valid and nothing was submitted, re-initialize
        # don't tell the user that fields are required if they haven't submitted anything!
        form = AdvancedSearchForm()

    # if form is invalid (no search terms) or there was an error, display search form
    response = render_to_response('fa/search_form.html',
                                  {'form': form, 'request': request},
                                  context_instance=RequestContext(request))
    # if query could not be parsed, set a 'Bad Request' status code on the response
    if query_error:
        response.status_code = 400
    return response


def document_search(request, id):
    "Keyword search on file-level items in a single Finding Aid."

    form = KeywordSearchForm(request.GET)
    query_error = False
    # get the findingaid - will 404 if not found
    # document/collection name required to generate document path
    ead = get_findingaid(id, only=['eadid', 'title',
                                   'document_name', 'collection_name'])
    if form.is_valid():
        search_terms = form.cleaned_data['keywords']
        try:
            # do a full-text search at the file level
            # include parent series information and enough ancestor series ids
            # in order to generate link to containing series at any level (c01-c03)

            # use path to restrict query to a single document (much faster)
            path = '%s/%s' % (ead.collection_name, ead.document_name)
            files = FileComponent.objects.filter(document_path=path)

            # at least one of search terms or dao may be present,
            # but both are optional

            # filter by keyword if present
            if search_terms:
                files = files.filter(fulltext_terms=search_terms)

            # restrict to publicly-accessible dao items, if set
            if form.cleaned_data['dao']:
                files = files.filter(did__dao_list__exists=True)
                # if user can view internal daos, no additional filter is needed
                # otherwise, restrict to publicly-accessible dao content
                if not request.user.has_perm('fa_admin.can_view_internal_dao'):
                    files = files.filter(public_dao_count__gte=1)

            files = files.also('parent__id', 'parent__did',
                               'series1__id', 'series1__did', 'series2__id', 'series2__did')

            # if there is a keyword search term, pass on for highlighting
            url_params = ''
            if search_terms:
                url_params = '?' + urlencode({'keywords': search_terms.encode('utf-8')})

            return render_to_response('fa/document_search.html', {
                'files': files,
                'ead': ead,
                'querytime': [files.queryTime(), ead.queryTime()],
                'keywords': search_terms,
                'dao': form.cleaned_data['dao'],
                'url_params': url_params,
                'docsearch_form': KeywordSearchForm(),
            }, context_instance=RequestContext(request))
        except ExistDBTimeout, e:
            # error for exist db timeout
            messages.error(request, "Your search has resulted in too many hits, \
                please make your terms more specific by using a direct phrase \
                search (e.g. \"Martin Luther King\").")
        except ExistDBException, e:
            # for an invalid full-text query (e.g., missing close quote), eXist
            # error reports 'Cannot parse' and 'Lexical error'
            # NOTE: some duplicate logic from error handling in main keyword search
            query_error = True
            if 'Cannot parse' in e.message():
                messages.error(request,
                               'Your search query could not be parsed.  ' +
                               'Please revise your search and try again.')
            else:
                # generic error message for any other exception
                messages.error(request, 'There was an error processing your search.')
    else:
        # invalid form
        messages.error(request, 'Please enter a search term.')
    # display empty search results
    response = render_to_response('fa/document_search.html', {
        'files': [],
        'ead': ead,
        'docsearch_form': KeywordSearchForm(),
    }, context_instance=RequestContext(request))
     # if query could not be parsed, set a 'Bad Request' status code on the response
    if query_error:
        response.status_code = 400
    return response


def _series_url(eadid, series_id, *ids, **extra_opts):
    """
    Generate a series or subseries url when given an eadid and list of series ids.
    Requires at least ead document id and top-level series id.  Number of additional
    series ids provided determines type of series url generated.

    Default url callback for :meth:`_subseries_links`.
    """
    # common args for generating all urls
    args = {'id': eadid, 'series_id': series_id}

    if len(ids) == 0:       # no additional args
        view_name = 'series-or-index'
    if len(ids) >= 1:       # add subseries id arg if one specified (used for sub and sub-subseries)
        args['series2_id'] = ids[0]
        view_name = 'series2'
    if len(ids) == 2:       # add sub-subseries id arg if specified
        args['series3_id'] = ids[1]
        view_name = 'series3'

    if 'preview' in extra_opts and extra_opts['preview'] is True:
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
    # namespaced tag names, for easy comparison of tag name to determine c-level
    C01 = '{%s}c01' % EAD_NAMESPACE
    C02 = '{%s}c02' % EAD_NAMESPACE
    C03 = '{%s}c03' % EAD_NAMESPACE

    # construct url ids if none are passed
    if url_ids is None:
        if not (series.ead and series.ead.eadid):
            raise Exception("Cannot construct subseries links without eadid for %s element %s"
                            % (series.node.tag, series.id))

        url_ids = [series.ead.eadid]

        # if c02/c03, check to ensure we have enough information to generate the correct link
        if series.node.tag in [C02, C03]:
            # if initial series passed in is c02 or c03, add c01 series id to url ids before current series id
            if hasattr(series, 'series') and series.series:
                url_ids.append(series.series.short_id)
            else:
                raise Exception("Cannot construct subseries links without c01 series id for %s element %s"
                                % (series.node.tag, series.id))

            if series.node.tag == C03:
                # if initial series passed in is c03, add c02 series id to url ids before current series id
                if hasattr(series, 'series2') and series.series2:
                    url_ids.append(series.series2.short_id)
                else:
                    raise Exception("Cannot construct subseries links without c02 subseries id for %s element %s"
                                    % (series.node.tag, series.id))

        #  current series id
        if series.node.tag in [C01, C02, C03]:
            url_ids.append(series.short_id)

    links = []
    if (hasattr(series, 'hasSubseries') and series.hasSubseries()) or \
       (hasattr(series, 'hasSeries') and series.hasSeries()):
        for component in series.c:
            # get match count for each series / subseries and append it to the link if > 0
            if component.match_count > 0:
                plural = "es" if component.match_count > 1 else ""
                match_count = "<span class='exist-match'>%s match%s</span>" % (component.match_count, plural)
            else:
                match_count = ""

            current_url_ids = url_ids + [component.short_id]
            #set c01 rel attrib to 'section' c02 and c03 to 'subsection'
            if (component.node.tag == C01):
                rel = 'section'
            elif (component.node.tag in [C02, C03]):
                rel = 'subsection'

            # don't include preview/keyword arg urls in RDFa rel
            if not url_params and not preview:
                rel += ' dcterms:hasPart'

            text = "<a href='%(url)s%(url_params)s' rel='%(rel)s'>%(linktext)s</a> %(match_count)s" % \
                {'url': url_callback(preview=preview, *current_url_ids),
                 'url_params': url_params,
                 'rel': rel,
                 'linktext':  component.display_label(), 'match_count': match_count}
            links.append(text)
            if component.hasSubseries():
                links.append(_subseries_links(component, url_ids=current_url_ids,
                                              url_callback=url_callback,
                                              preview=preview, url_params=url_params))
    return links
