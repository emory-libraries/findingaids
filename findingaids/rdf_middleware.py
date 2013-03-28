import rdflib
from django.core.urlresolvers import resolve
from django.http import Http404, HttpResponse


class RDFaMiddleware(object):
    '''Middleware to display embedded RDFa for an HTML page as
    RDF XML.  Simply add ``rdf/`` to the end of any Django site
    URL to see the RDF XML version of RDFa embedded in the page.

    '''

    def process_request(self, request):
        if request.path.endswith('/rdf/'):
            print 'path %s ends with rdf' % request.path
            # load the html for the non-rdf page
            base_url = request.path[:-4]  # strip off 'rdf/' from end
            view, args, kwargs = resolve(base_url)
            kwargs['request'] = request
            try:
                result = view(*args, **kwargs)
            except Http404:
                return None

            g = rdflib.ConjunctiveGraph()
            # TODO: probably should only attempt to parse RDFa
            # from HTML pages (e.g., not PDF, etc)
            g.parse(data=result.content, format='rdfa')
            # only return rdf if graph contains triples
            if len(g):
                return HttpResponse(g.serialize(),
                                    content_type='application/rdf+xml')

        return None
