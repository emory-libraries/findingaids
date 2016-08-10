# file findingaids/fa/utils.py
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

from datetime import datetime
from functools import wraps
import logging
from lxml import etree
import os
import re
import subprocess
import tempfile

from django import http
from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import get_object_or_404

from django.template import RequestContext

from eulexistdb.exceptions import DoesNotExist  # ReturnedMultiple needed also ?

from findingaids.fa.models import FindingAid, Deleted

logger = logging.getLogger(__name__)

# parse and load XSLT for converting html to XSL-FO at init
xhtml_xslfo_xslt = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'xhtml_to_xslfo.xsl')
XHTML_TO_XSLFO = etree.XSLT(etree.parse(xhtml_xslfo_xslt))


def render_to_pdf(template_src, context_dict, filename=None):
    """Generate and return a PDF response.

    Takes a template and template arguments; the template is rendered as html,
    converted to XSL-FO, which is run through the configured XSL-FO processor to
    generate a PDF.  Any template used with this function should produce
    well-formed xhtml so it can be parsed as xml.

    :param template_src: name of the template to render
    :param context_dict: dictionary to pass to the template for rendering
    :param filename: optional filename, to specify to the browser in the response
    :returns: :class:`django.http.HttpResponse` with PDF content, content-type,
            and, if a filename was specified, a content-disposition header to
            prompt the browser to download the response as the filename specified
    """

    xslfo = html_to_xslfo(template_src, context_dict)
    tmpdir = tempfile.mkdtemp('findingaids-fop')
    # write xsl-fo to a temporary named file that we can pass to xsl-fo processor
    xslfo_file = tempfile.NamedTemporaryFile(prefix='findingaids-xslfo-', dir=tmpdir)
    logger.debug("Writing out XSL-FO to %s" % xslfo_file.name)
    xslfo.write(xslfo_file.name, encoding='UTF-8', pretty_print=True, xml_declaration=True)
    # create a temporary file where the PDF should be created
    pdf_file = tempfile.NamedTemporaryFile(prefix='findingaids-pdf-', dir=tmpdir)
    # create a log4j file so we can get fop errors
    # FIXME: there must be a better way to dot his!
    log4j_prop = os.path.join(tmpdir, 'log4j.properties')
    with open(log4j_prop, 'w') as file:
        file.write('log4j.rootLogger=%s, CONSOLE' % ('WARN' if settings.DEBUG else 'ERROR') + '''
log4j.appender.CONSOLE=org.apache.log4j.ConsoleAppender
log4j.appender.CONSOLE.layout=org.apache.log4j.PatternLayout
log4j.appender.CONSOLE.layout.ConversionPattern=%-5p %3x - %m%n
        ''')
    try:
        # NOTE: for now, just sending errors to stdout
        cmd_parts = [settings.XSLFO_PROCESSOR, xslfo_file.name, pdf_file.name]
        logger.debug("Calling XSL-FO processor: %s" % ' '.join(cmd_parts))
        rval = subprocess.call(cmd_parts, cwd=tmpdir)
        if rval is 0:       # success!
            response = http.HttpResponse(pdf_file.read(), content_type='application/pdf')
            if filename:
                response['Content-Disposition'] = "inline; filename=%s" % filename
            return response
    except OSError, e:
        logger.error("Apache Fop execution failed: %s" % e)
    finally:
        # clean up tmp files
        os.unlink(log4j_prop)
        # temporary files are automatically deleted when closed
        xslfo_file.close()
        # can get an OSError if the PDF file does not exist, e.g. if fop failed
        try:
            pdf_file.close()
        except OSError, e:
            logger.error("Failed to delete temporary PDF file: %s" % e)
        finally:
            # dir should be empty now, so we can delete it
            os.rmdir(tmpdir)

    # if nothing was returned by now, there was an error generating the pdf
    raise Exception("There was an error generating the PDF")


def html_to_xslfo(template_src, context_dict):
    """Takes a template and template arguments, renders the template to get html,
    and then converts from html to XSL-FO.  Any template used with this function
    should produce well-formed xhtml so it can be parsed as xml.

    :param template_src: name of the template to render
    :param context_dict: dictionary to pass to the template for rendering
    :returns: result of generated html, converted to XSL-FO, as an instance of
                :class:`lxml.etree.ElementTree`
    """
    template = get_template(template_src)
    xhtml = etree.fromstring(template.render(Context(context_dict)))
    xsl_params = {
        'STATIC_ROOT': settings.STATIC_ROOT,
        'STATIC_URL': settings.STATIC_URL,
        'link_color': '#2e5299',   # match CSS for site
    }
    if not xsl_params['STATIC_ROOT'].endswith('/'):
        xsl_params['STATIC_ROOT'] += '/'
    # string values need to be quoted to pass as xsl params
    for k, v in xsl_params.iteritems():
        xsl_params[k] = "'%s'" % v
    return XHTML_TO_XSLFO(xhtml, **xsl_params)


def pages_to_show(paginator, page, page_labels={}):
    """Generate a dictionary of pages to show around the current page. Show
    3 numbers on either side of the specified page, or more if close to end or
    beginning of available pages.

    :param paginator: paginator object, populated with objects
    :param page: number of the current page
    :param page_labels: optional dictionary of page labels, keyed on page number
    :rtype: dictionary
    """
    show_pages = {}
    if page != 1:
        before = 3      # default number of pages to show before the current page
        if page >= (paginator.num_pages - 3):   # current page is within 3 of end
            # increase number to show before current page based on distance to end
            before += (3 - (paginator.num_pages - page))
        for i in range(before, 0, -1):    # add pages from before away up to current page
            if (page - i) >= 1:
                # if there is a page label available, use that as dictionary value
                show_pages[page - i] = page_labels[page - i ] if (page - 1) in page_labels else None
    # show up to 3 to 7 numbers after the current number, depending on how many we already have
    for i in range(7 - len(show_pages)):
        if (page + i) <= paginator.num_pages:
            # if there is a page label available, use that as dictionary value
            show_pages[page + i] = page_labels[page + i] if (page + i) in page_labels else None

    return show_pages

def alpha_pagelabels(paginator, objects, label_attribute):
    """Generate abbreviated, alphabetical page labels for pagination items.
    Label format should be something like 'Ab - Ad', 'Ard - Art'.

    :param paginator: a django paginator
    :param objects: the complete list of objects paginated by the paginator
    :param label_attribute: attribute on the object to use to generate
        page labels
    :returns: dictionary appropriate for use with :meth:`pages_to_show`, keyed
        on page numbers
    """
    page_labels = {}
    labels = []

    if paginator.count <= 1:
        # if there is not enough content to paginate, bail out
        return page_labels

    # get all labels for start and end objects on each page
    for i in range(paginator.num_pages):
        page = paginator.page(i+1)  # page is 1-based
        # get objects at start & end of each page (index is also 1-based)
        labels.append(unicode(getattr(objects[page.start_index()-1], label_attribute)))
        # don't go beyond the end of the actual number of objects
        end_index = min(page.end_index()-1, paginator.count)
        # add end label only if not the same as first (e.g., page of a single item)
        if page.start_index() - 1 != end_index:
            labels.append(unicode(getattr(objects[end_index], label_attribute)))

    # abbreviate labels so they are as short as possible but distinct from
    # preceding and following labels
    abbreviated_labels = []
    for i in range(len(labels)):
        for j in range(1, len(labels[i])+1):
            # start with one letter, go up to full length of the label if necessary
            abbr = labels[i][:j]
            next_label = labels[i+1] if i+1 < len(labels) else ''
            prev_label = labels[i-1] if i > 0 else ''
            if abbr != next_label[:j] and abbr != prev_label[:j]:
                # at current length, abbreviation is different from neighboring labels
                abbreviated_labels.append(abbr)
                break
            elif labels[i] == next_label or labels[i] == prev_label:
                # In the rare case that two labels are *exactly* the same,
                # add the full label.
                # In finding aids, this is most likely to happen with origination name;
                # remove trailing dates in these formats: , NNNN-NNN. , NNNN. , NNNN-
                label = re.sub(r', \d{4}-?(\d{4})?.?$', '', labels[i])
                abbreviated_labels.append(label)
                break
            elif j == len(labels[i]):
                # If we get to the end of the label and have not met another
                # case, just use the whole label.
                # Only happens in rare cases, e.g. when there is a nearly
                # complete match like variant titles with and without
                # trailing period.
                abbreviated_labels.append(abbr)

    for i in range(0, len(abbreviated_labels), 2):
        page_index = (i+2) / 2
        try:
            page_labels[page_index] = '%s - %s' % (abbreviated_labels[i].strip(),
                                                  abbreviated_labels[i+1].strip())
        except IndexError:
            # paginator was not created with orphan protection,
            # it's possible we could get a single item at the end
            page_labels[page_index] = abbreviated_labels[i].strip()

    return page_labels

def get_findingaid(eadid=None, preview=False, only=None, also=None, order_by=None,
        filter=None):
    """Retrieve a  :class:`~findingaids.fa.models.FindingAid` (or
    :class:`~findingaids.fa.models.FindingAid`  :class:`eulexistdb.manager.Manager`)
    from eXist by eadid, with any query options specified.  Raises a
    :class:`django.http.Http404` if the requested document is not found in eXist.

    Handles switching to preview collection and then switching back when
    preview is set to True.

    :param eadid: eadid of the :class:`~findingaids.fa.models.FindingAid` to
            retrieve; if not specified, a :class:`eulexistdb.manager.Manager`
            will be returned instead
    :param preview: optional; set to True to load the finding aid from the
            preview collection; defaults to False
    :param only: optional list of fields to return (**only** return the specified fields)
    :param also: optional list of additional fields to return
    :param order_by: optional field to use for sorting
    :param filter: optional queryset filter to apply, in dictionary form
    :returns: :class:`~findingaids.fa.models.FindingAid` (when eadid is specified)
            or a :class:`~findingaids.fa.models.FindingAid` :class:`eulexistdb.manager.Manager`
            (if no eadid is specified)
    """
    try:
        fa = FindingAid.objects.all()   # make sure we always have a queryset to start with
        if only is not None:
            fa = fa.only(*only)
        if also is not None:
            fa = fa.also(*also)
        if order_by is not None:
            fa = fa.order_by(order_by)
        if filter is not None:
            fa = fa.filter(**filter)
        if preview:
            fa = fa.using(settings.EXISTDB_PREVIEW_COLLECTION)
        if eadid is not None:
            fa = fa.get(eadid=eadid)
    except DoesNotExist:
        raise http.Http404
    return fa


def ead_lastmodified(request, id, preview=False, *args, **kwargs):
    """Get the last modification time for a finding aid in eXist by eadid.
    Used to generate last-modified header for views based on a single EAD document.

    :param id: eadid
    :param preview: load document from preview collection; defaults to False
    :rtype: :class:`datetime.datetime`
    """
    # get document name last modified by eadid
    fa = get_findingaid(id, preview=preview, only=['last_modified'])
    return exist_datetime_with_timezone(fa.last_modified)


def ead_etag(request, id, preview=False, *args, **kwargs):
    """Generate an Etag for an ead (specified by eadid) by requesting a SHA-1
    checksum of the entire EAD xml document from eXist.

    :param id: eadid
    :param preview: requested document is in the preview collection; defaults to False
    :rtype: string
    """
    fa = get_findingaid(id, preview=preview, only=['hash'])
    return fa.hash

def collection_lastmodified(request, *args, **kwargs):
    """Get the last modification time for the entire finding aid collection.
    Used to generate last-modified header for views that are based on the entire
    collection (e.g., :meth:`~findingaids.fa.views.titles_by_letter` browse view,
    :meth:`findingaids.fa.views.search` search view).

    If no documents are found in eXist and there are no deleted records, no
    value is returned and django will not send a Last-Modified header.
    """
    fa_last = None
    # most recently modified document in the eXist collection
    fa = FindingAid.objects.order_by('-last_modified').only('last_modified')
    if fa .count():
        fa_last = fa[0].last_modified
    # most recently deleted document from sql DB
    deleted = Deleted.objects.order_by('-date').all()
    if deleted.exists():
        deleted_last = deleted[0].date
        # get most recent of the two
        if fa_last is None or deleted_last > fa_last:
            fa_last = deleted_last
    if fa_last is not None:
        # NOTE: potentially using configured exist TZ for non-eXist date...
        return exist_datetime_with_timezone(fa_last)

# object pagination - adapted directly from django paginator documentation
def paginate_queryset(request, qs, per_page=10, orphans=0):    # 0 is django default
    # FIXME: should num-per-page be configurable via local settings?
    paginator = Paginator(qs, per_page, orphans=orphans)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    # If page request (9999) is out of range, deliver last page of results.
    try:
        paginated_qs = paginator.page(page)
    except InvalidPage:
        raise http.Http404
    except EmptyPage:       # ??
        paginated_qs = paginator.page(paginator.num_pages)

    return paginated_qs, paginator

def ead_gone_or_404(view_method):
    """This decorator is intended for use with single-ead views to determine if
    an EAD not found in eXist is gone or really not found.  If a requested
    EAD document is not found in the eXist database, the view method should raise
    a :class:`django.http.Http404` exception.  This decorator will catch that
    and check for a deleted record which indicates the EAD has been removed.

    View method is expected to take a request parameter and an eadid.

    Raises an :class:`django.http.Http404` when requested EAD was not found in
    the original view method and no deleted record was found.

    :return: :class:`django.http.HttpResponse` with status 410 and a notice
            indicating that the document has been removed
    """
    @wraps(view_method)
    def decorator (request, id, *args, **kwargs):
        try:
            return view_method(request, id, *args, **kwargs)
        except http.Http404:
            # not found in eXist - check for a deleted record
            deleted = get_object_or_404(Deleted, eadid=id)
            t = get_template('fa/deleted.html')
            return http.HttpResponseGone(t.render(RequestContext(request,
                                                        {'deleted' : deleted})))
    return decorator

def exist_datetime_with_timezone(dt):
    """Convert an 'offset-naive' datetime object into an 'offset-aware' datetime
    using a configured timezone.

    The current version of xmlrpclib ignores timezones, which messes up dates
    (e.g., when used for last-modified header).  This function uses a configured
    timezone from django settings to convert a datetime to offset-aware.
    """
    tz = settings.EXISTDB_SERVER_TIMEZONE
    # use the exist time and configured timezone to create a timezone-aware datetime
    return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                    dt.second, dt.microsecond, tz)


