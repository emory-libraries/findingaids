import httplib
from time import sleep
from celery.decorators import task

from django.conf import settings
from django.core.urlresolvers import reverse

@task
def reload_cached_pdf(eadid):
    """Request the PDF of the finding aid (specified by eadid) from the configured
    proxy server, to trigger the proxy reloading and caching the latest version
    of that PDF (e.g., after updating or adding a new document in eXist)."""
    logger = reload_cached_pdf.get_logger()
    if hasattr(settings, 'PROXY_HOST') and hasattr(settings, 'SITE_BASE_URL'):
        sleep(3)    # may need to sleep for a few seconds so cache will recognized as modified (?)
        connection = httplib.HTTPConnection(settings.PROXY_HOST)
        url = "%s%s" % (settings.SITE_BASE_URL.rstrip('/'), reverse('fa:printable', kwargs={'id': eadid }))
        logger.info("Requesting PDF for %s from configured cache at %s" % (eadid, url))
        # set headers to force the cache to get a fresh copy
        refresh_cache = {
            # tell the cache to grab a fresh copy (implied: cache the fresh copy)
            'Cache-Control': 'max-age=0'
            # NOTE: using Cache-Control: no-cache clears the cache but does not populate
            }
        connection.request('GET', url, None, refresh_cache)     # no request body, cache header
        r = connection.getresponse()    # actually get the response to trigger PDF generation
        if r.status == 200:
            return True
        else:
            raise Exception("Got unexpected HTTP status code from response: %s" % r.status)
    else:
        raise Exception("PROXY_HOST and/or SITE_BASE_URL settings not available.  Failed to reload cached PDF.")

