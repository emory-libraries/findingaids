# file findingaids/fa_admin/tasks.py
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

import urllib2
from time import sleep
from celery import task

from django.conf import settings
from django.core.urlresolvers import reverse

from findingaids import __version__ as SW_VERSION


@task
def reload_cached_pdf(eadid):
    """Request the PDF of the finding aid (specified by eadid) from the configured
    proxy server, to trigger the proxy reloading and caching the latest version
    of that PDF (e.g., after updating or adding a new document in eXist)."""
    logger = reload_cached_pdf.get_logger()
    if hasattr(settings, 'PROXY_HOST') and hasattr(settings, 'SITE_BASE_URL'):
        sleep(3)    # may need to sleep for a few seconds so cache will recognized as modified (?)
        url = "%s%s" % (settings.SITE_BASE_URL.rstrip('/'),
            reverse('fa:printable', kwargs={'id': eadid}))
        logger.info("Requesting PDF for %s from configured cache at %s" % (eadid, url))
        # set headers to force the cache to get a fresh copy
        basic_headers = {
            'User-Agent': 'FindingAids PDF Reloader/%s' % SW_VERSION,
            'Accept': '*/*',
        }
        refresh_cache = {
            # tell the cache to grab a fresh copy (implied: cache the fresh copy)
            'Cache-Control': 'max-age=0',
            # squid doesn't seem to cache the new version when we specify no-cache,
            # even though that is not what the spec says no-cache means
            #'Pragma': 'no-cache',
        }
        refresh_cache.update(basic_headers)
        logger.debug('Request headers: \n%s' % \
                     '\n'.join(['\t%s: %s' % header for header in refresh_cache.iteritems()]))
        # enable the configured proxy
        urllib2.ProxyHandler({'http': settings.PROXY_HOST})
        request = urllib2.Request(url, None, refresh_cache)
        response = urllib2.urlopen(request)
        logger.debug('Response headers: \n%s' % response.info())

        if response.code != 200:
            raise Exception("Got unexpected HTTP status code from response: %s" \
                            % response.code)
        return True

    else:
        raise Exception("PROXY_HOST and/or SITE_BASE_URL settings not available.  Failed to reload cached PDF.")
