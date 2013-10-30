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
import os.path
import shutil
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from eullocal.django.taskresult.models import TaskResult

from findingaids import __version__ as SW_VERSION
from findingaids.fa.models import Archive
from findingaids.fa_admin.svn import svn_client


logger = logging.getLogger(__name__)

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


@task
def archive_svn_checkout(archive, update=False):
    client = svn_client()

    # if this is an update, clear out existing svn checkout
    if update and os.path.isdir(archive.svn_local_path):
        shutil.rmtree(archive.svn_local_path)
        logger.info('removing outdated svn directory %s' %
                    archive.svn_local_path)

    client.checkout(archive.svn, archive.svn_local_path, 'HEAD')
    # NOTE: could return brief text here to indicate more about what was done
    # (update / initial checkout), for display in task result list


@receiver(post_save, sender=Archive)
def archive_save_hook(sender, instance, created, raw, using,
                      update_fields, **kwargs):
    # check if an svn update or checkout is needed before queuing the task
    updated = False
    if not created:
        # if path already exists, check if the svn url has changed
        if os.path.isdir(instance.svn_local_path):
            client = svn_client()
            svninfo = client.info(instance.svn_local_path, depth=0)
            current_svn_url = svninfo[svninfo.keys()[0]].url
            if current_svn_url != instance.svn:
                updated = True

    if created or updated:
        result = archive_svn_checkout.delay(instance, update=updated)
        task = TaskResult(label='SVN checkout',
            object_id=instance.label,  # will be displayed in task result
            url=reverse('admin:fa_archive_change', args=[instance.pk]), # link in task result
            task_id=result.task_id)
        task.save()
