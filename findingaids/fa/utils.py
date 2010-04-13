# adapted from django snippets example - http://www.djangosnippets.org/snippets/659/
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
import ho.pisa as pisa
import cStringIO as StringIO
import cgi
from django import http

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

