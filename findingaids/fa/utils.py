import ho.pisa as pisa
import cStringIO as StringIO
import cgi
from datetime import datetime
from functools import wraps

from django import http
from django.conf import settings
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import get_object_or_404

from django.template import RequestContext

from eulcore.django.existdb.db import ExistDB
from eulcore.existdb.exceptions import DoesNotExist # ReturnedMultiple needed also ?

from findingaids.fa.models import FindingAid, Deleted

# adapted from django snippets example - http://www.djangosnippets.org/snippets/659/
def render_to_pdf(template_src, context_dict, filename=None):
    template = get_template(template_src)
    context = Context(context_dict)
    # set media root in context - css and images must have full file paths for PDF generation
    context['MEDIA_ROOT'] = settings.MEDIA_ROOT
    html  = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("utf-8")), result)
    if not pdf.err:
        response = http.HttpResponse(result.getvalue(), mimetype='application/pdf')
        if filename:
            response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    # FIXME: this error handling probably needs some work
    print "ERR", pdf.err
    return http.HttpResponse('Error generating PDF')
    return http.HttpResponse('Error generating PDF<pre>%s</pre>' % cgi.escape(html))

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


# functionality for switching to preview mode

_stored_publish_collection = None

def use_preview_collection():
    # for preview mode: store real exist collection, and switch to preview collection
    global _stored_publish_collection
    _stored_publish_collection = getattr(settings, "EXISTDB_ROOT_COLLECTION", None)

    # temporarily override settings
    settings.EXISTDB_ROOT_COLLECTION = settings.EXISTDB_PREVIEW_COLLECTION
    db = ExistDB()
    # create preview collection, but don't complain if it already exists
    db.createCollection(settings.EXISTDB_ROOT_COLLECTION, overwrite=True)

def restore_publish_collection():
    # for preview mode: switch back to real exist collection
    global _stored_publish_collection

    if _stored_publish_collection is not None:
        settings.EXISTDB_ROOT_COLLECTION = _stored_publish_collection

def get_findingaid(eadid=None, preview=False, only=None, also=None, order_by=None,
        filter=None):
    """Retrieve a  :class:`~findingaids.fa.models.FindingAid` (or
    :class:`~findingaids.fa.models.FindingAid`  :class:`eulcore.django.existdb.manager.Manager`)
    from eXist by eadid, with any query options specified.  Raises a 
    :class:`django.http.Http404` if the requested document is not found in eXist.

    Handles switching to preview collection and then switching back when
    preview is set to True.

    :param eadid: eadid of the :class:`~findingaids.fa.models.FindingAid` to
            retrieve; if not specified, a :class:`eulcore.django.existdb.manager.Manager`
            will be returned instead
    :param preview: optional; set to True to load the finding aid from the
            preview collection; defaults to False
    :param only: optional list of fields to return (**only** return the specified fields)
    :param also: optional list of additional fields to return
    :param order_by: optional field to use for sorting
    :param filter: optional queryset filter to apply, in dictionary form
    :returns: :class:`~findingaids.fa.models.FindingAid` (when eadid is specified)
            or a :class:`~findingaids.fa.models.FindingAid` :class:`eulcore.django.existdb.manager.Manager`
            (if no eadid is specified)
    """
    if preview:
        use_preview_collection()
    try:
        fa = FindingAid.objects
        if only is not None:
            fa = fa.only(*only)
        if also is not None:
            fa = fa.also(*also)
        if order_by is not None:
            fa = fa.order_by(order_by)
        if filter is not None:
            fa = fa.filter(**filter)
        if eadid is not None:
            fa = fa.get(eadid=eadid)
    except DoesNotExist:
        raise http.Http404
    finally:
        # collection setting should be restored no matter what goes wrong
        if preview:    
            restore_publish_collection()
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
    Used to generate last-modified header for :meth:`~findingaids.fa.views.titles_by_letter` view.
    """
    # most recently modified document in the eXist collection
    fa_last = FindingAid.objects.order_by('-last_modified').only('last_modified')[0].last_modified
    # most recently deleted document from sql DB
    deleted = Deleted.objects.order_by('-date').all()
    if deleted.exists():
        deleted_last = deleted[0].date
        # get most recent of the two
        if deleted_last > fa_last:            
            fa_last = deleted_last
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
            t = get_template('findingaids/deleted.html')
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