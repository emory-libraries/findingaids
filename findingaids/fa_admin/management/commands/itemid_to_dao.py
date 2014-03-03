# file findingaids/fa_admin/management/commands/itemid_to_dao.py
#
#   Copyright 2014 Emory University Library
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

import glob
import httplib2
from lxml.etree import XMLSyntaxError
import os
import re
import sunburnt
from urlparse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulxml.xmlmap import eadmap
from eulxml.xmlmap.core import load_xmlobject_from_file

from findingaids.fa.models import FindingAid, Archive
from findingaids.fa_admin.svn import svn_client

class Command(BaseCommand):
    """Replace container-level item digital item ids with dao tags.

Looks through the container level item description of EAD xml files
to identify filename references in the unitid, look up those identifiers
in the Keep, and replace the note with one or more <dao> tags using the
ARK url for the identified item.

If filenames are specified as arguments, only those files will be prepared.
Files should be specified by full path. Otherwise, all .xml files in each of
the defined Archives will be prepared."""
    help = __doc__

    args = '[<filename filename ... >]'

    # django default verbosity level options --  1 = normal, 0 = minimal, 2 = all
    v_normal = 1

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity', self.v_normal))

        # check for required settings
        if not hasattr(settings, 'KEEP_SOLR_SERVER_URL') or not settings.KEEP_SOLR_SERVER_URL:
            raise CommandError("KEEP_SOLR_SERVER_URL setting is required for this script")
            return

        solr = solr_interface()

        if verbosity > self.v_normal:
            print "Preparing documents from all defined Archives"

        updated = 0
        unchanged = 0
        errored = 0

        if len(args):
            files = args
        else:
            # Note: copied from prep_ead manage command; move somewhere common?
            files = set()
            svn = svn_client()
            for archive in Archive.objects.all():
                # update to make sure we have latest version of everything
                svn.update(str(archive.svn_local_path))   # apparently can't handle unicode
                files.update(set(glob.iglob(os.path.join(archive.svn_local_path, '*.xml'))))

        # regex for recognizing digitized content
        digitized_ids = re.compile('\[digitized;? (Emory|filename):?\s*(?P<ids>[0-9a-z-, ]+)\s*\]', re.IGNORECASE)

        for file in files:
            try:
                ead = load_xmlobject_from_file(file, FindingAid)
                orig_xml = ead.serializeDocument(pretty=True)  # keep to check if changed

                for c in self.ead_file_items(ead):
                    # print unicode(c.did.unittitle)
                    # TODO: may want to move into class methods to make easier to test
                    match = digitized_ids.search(unicode(c.did.unittitle))
                    if match:
                        print unicode(c.did.unittitle)
                        ids = match.groupdict()['ids']
                        # check what kind of id(s) are listed

                        # comma-separated list
                        if ',' in ids:
                            id_list = [i.strip() for i in ids.split(',')]

                        # range of numbers
                        elif '-' in ids:
                            start, stop = [i.strip() for i in ids.split('-')]
                            length = len(start)
                            # use range to get an inclusive list of the ids
                            # then reformat with the same number of leading 000s
                            fmt = '%%0%dd' % length
                            id_list = [fmt % i for i in range(int(start), int(stop) + 1)]

                        # otherwise, must be a single id listed only
                        else:
                            id_list = [ids.strip()]

                        print id_list
                        found_list = []

                        for i in id_list:
                            q = solr.query(solr.Q(dm1_id="%s" % i) | solr.Q(pid="%s" % i)) \
                                    .field_limit(['ark_uri', 'pid'])
                            if q.count() == 1:
                                found_list.append(q[0])
                                print '*** %d matches for id %s' % (q.count(), i)
                                print q[0]['ark_uri']

                        # if we found a keep item for every id, then proceed
                        if len(id_list) == len(found_list):
                            # remove the plain-text digitized ids from unittitle
                            # FIXME: check if there is a unitdate?
                            c.did.unittitle.text = re.sub(digitized_ids, '', c.did.unittitle.text)
                            # append a new dao for each found item
                            for info in found_list:
                                c.did.dao_list.append(eadmap.DigitalArchivalObject(id=info['pid'],
                                    href=info['ark_uri'], audience='internal'))

                if orig_xml == ead.serializeDocument(pretty=True):
                    if verbosity >= self.v_normal:
                        print "No changes made to %s" % file
                    unchanged += 1
                else:
                    with open(file, 'w') as f:
                        ead.serializeDocument(f, pretty=True)
                    if verbosity >= self.v_normal:
                        print "Updated %s" % file
                    updated += 1

            except XMLSyntaxError:
                # xml is not well-formed
                print "Error: failed to load %s (document not well-formed XML?)" \
                            % file
                errored += 1
            # except Exception, e:
            #     # catch any other exceptions
            #     print "Error: failed to update %s : %s" % (file, e)
            #     errored += 1

        # TODO: might be nice to also report total number of daos added

        # summary of what was done
        print "%d document%s updated" % (updated, 's' if updated != 1 else '')
        print "%d document%s unchanged" % (unchanged, 's' if unchanged != 1 else '')
        print "%d document%s with errors" % (errored, 's' if errored != 1 else '')

    def ead_file_items(self, ead):
        '''generator that returns all file-level components in a findingaid,
        including any in series or subseries.
        '''
        if ead.dsc.hasSeries():
            for c in ead.dsc.c:
                for subc in self.series_file_items(c):
                    yield subc
        else:
            for c in ead.dsc.c:
                yield c

    def series_file_items(self, series):
        '''generator that returns all file-level components in a series,
        including any in subseries'''
        if series.hasSubseries():
            for c in series.c:
                for subc in self.series_file_items(c):
                    yield subc
        else:
            for c in series.c:
                yield c


def solr_interface():
    '''Wrapper function to initialize a
    :class:`sunburnt.SolrInterface` based on django settings and
    evironment.  Uses **KEEP_SOLR_SERVER_URL** and **SOLR_CA_CERT_PATH** if
    one is set.  Additionally, if an **HTTP_PROXY** is set in the
    environment, it will be configured.
    '''
    # NOTE: borrowed pretty much intact from keep.util
    http_opts = {}
    if hasattr(settings, 'SOLR_CA_CERT_PATH'):
        http_opts['ca_certs'] = settings.SOLR_CA_CERT_PATH
    if getattr(settings, 'SOLR_DISABLE_CERT_CHECK', False):
        http_opts['disable_ssl_certificate_validation'] = True

    # use http proxy if set in ENV
    http_proxy = os.getenv('HTTP_PROXY', None)
    solr_url = urlparse(settings.KEEP_SOLR_SERVER_URL)
    # NOTE: using Squid with httplib2 requires no-tunneling proxy option
    # - non-tunnel proxy does not work with https
    if http_proxy and solr_url.scheme == 'http':
        parsed_proxy = urlparse(http_proxy)
        proxy_info = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL,
                                        proxy_host=parsed_proxy.hostname,
                                        proxy_port=parsed_proxy.port)
        http_opts['proxy_info'] = proxy_info
    http = httplib2.Http(**http_opts)

    solr_opts = {'http_connection': http}

    solr = sunburnt.SolrInterface(settings.KEEP_SOLR_SERVER_URL,
                                  **solr_opts)
    return solr

