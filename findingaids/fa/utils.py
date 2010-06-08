import ho.pisa as pisa
import cStringIO as StringIO
import cgi

from django import http
from django.conf import settings
from django.template import Context
from django.template.loader import get_template

from eulcore.django.existdb.db import ExistDB

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
    print "ERR", pdf.err
    return http.HttpResponse('Error generating PDF')
    return http.HttpResponse('Error generating PDF<pre>%s</pre>' % cgi.escape(html))

# functionality for switching to preview mode

_stored_publish_collection = None

def _use_preview_collection():
    # for preview mode: store real exist collection, and switch to preview collection
    global _stored_publish_collection
    _stored_publish_collection = getattr(settings, "EXISTDB_ROOT_COLLECTION", None)

    # temporarily override settings
    settings.EXISTDB_ROOT_COLLECTION = settings.EXISTDB_PREVIEW_COLLECTION
    db = ExistDB()
    # create test collection, but don't complain if collection already exists
    db.createCollection(settings.EXISTDB_ROOT_COLLECTION, True)

def _restore_publish_collection():
    # for preview mode: switch back to real exist collection
    global _stored_publish_collection

    if _stored_publish_collection is not None:
        settings.EXISTDB_ROOT_COLLECTION = _stored_publish_collection
