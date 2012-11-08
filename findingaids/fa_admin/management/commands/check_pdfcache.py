# file findingaids/fa_admin/management/commands/check_pdfcache.py
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

from datetime import timedelta
import httplib
from optparse import make_option
import socket
import struct
from zc import icp

from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.conf import settings

from findingaids.fa.models import FindingAid

# Internet Cache Protocol OP codes
ICP_DENIED = 'ICP_OP_DENIED'
ICP_ERROR = 'ICP_OP_ERR'
ICP_HIT = 'ICP_OP_HIT'
ICP_MISS = 'ICP_OP_MISS'

class Command(BaseCommand):
    """Check status of Finding Aid PDFs in the configured cache.  If any eadids 
are specified, checks only those documents; otherwise, checks all published
Finding Aids, up to any maximum number specified.

In verbose mode, reports the cache age and any warnings for cached items."""
    help = __doc__

    args = '[<eadid eadid ... >]'

    option_list = BaseCommand.option_list + (
        make_option('--max', '-m',
            dest='max',
            metavar='##',
            type='int',
            help='Check only the specified number of PDFs'),
        )

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1

        # check for required settings
        if not hasattr(settings, 'PROXY_HOST'):
            raise CommandError('PROXY_HOST setting is missing')
        if not hasattr(settings, 'SITE_BASE_URL'):  # could be empty
            raise CommandError('SITE_BASE_URL setting is missing')
        if not hasattr(settings, 'PROXY_ICP_PORT') or not settings.PROXY_ICP_PORT:
            raise CommandError('PROXY_ICP_PORT setting is missing')

        if verbosity >= v_normal:
            print "Checking status of printable Finding Aid in configured cache",  \
                    '- stopping after %d' % options['max'] if options['max'] else ''

        # http connection - retrive more info for cached items
        connection = httplib.HTTPConnection(settings.PROXY_HOST)

        # create a socket connection to cache server's ICP port for querying
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        proxy_host = settings.PROXY_HOST
        if ':' in proxy_host:
            # proxy may be specified as hostname:port but we don't want to use that port
            proxy_host, proxy_port = proxy_host.split(':')
        base_url = settings.SITE_BASE_URL.rstrip('/')
        if base_url == '':
            # use proxy hostname as base url (e.g., cache is running as transparent proxy)
            base_url = 'http://%s' % proxy_host
        if verbosity > v_normal:
            print "Connecting to cache ICP on %s:%s" % (proxy_host, settings.PROXY_ICP_PORT)
        s.connect((proxy_host, settings.PROXY_ICP_PORT))
      
        count = 0
        hit = 0
        miss = 0
        result_fmt = '%(eadid)30s\t%(status)s'

        # use any eadids specified, otherwise get finding aids from db
        if len(args):
            eadids = args
        else:
            # should we use any kind of sorting here ?
            findingaids = FindingAid.objects.all()
            eadids = (ead.eadid.value for ead in findingaids)

        for eadid in eadids:
            # ead printable url to check in the cache
            pdf_url = reverse('fa:printable', kwargs={'id': eadid })
            url = "%s%s" % (base_url, pdf_url)
            # construct ICP query 
            query = icp.HEADER_LAYOUT + icp.QUERY_LAYOUT
            # url in ICP struct must be null-terminated
            q_url =  "%s\0" % url
            format = query % len(q_url)
            icp_request = struct.pack(
                format, 1, 2, struct.calcsize(format),
                count,          # request number
                0, 0, 0, 0,     # request url - 0.0.0.0 for not specified
                url)
            s.send(icp_request)
            icp_response = s.recv(16384)
            # for debugging, uncomment this to see response structure
            #print icp.format_datagram(icp_response)
            code, request_no = icp_response_info(icp_response)
            # make sure response matches request number we expect
            while request_no != count:
                # note: this could potentially block, but that should be unlikely
                icp_response = s.recv(16384)
                code, request_no = icp_response_info(icp_response)

            # verbose mode - print url being tested (e.g., for manual comparison)
            if verbosity > v_normal:
                print url

            # if ICP is denied or error, bail out
            if code == ICP_DENIED:
                print "Error: got response code %s -- check that proxy is configured to allow ICP queries from this host" % code
                return
            elif code == ICP_ERROR:
                print "Error: got response code %s -- script may not be querying URLs correctly" % code
                return          
                
            # display eadid and response code returned from cache
            # normal verbosity: display non-hits only; verbose: print all
            if verbosity > v_normal or (verbosity == v_normal and code != ICP_HIT):
                print result_fmt % {'eadid': eadid, 'status': code}            

            if code == ICP_HIT:
                hit += 1
                # in verbose mode, get more info from cache via headers
                if verbosity > v_normal:
                    connection.request('HEAD', pdf_url)
                    r = connection.getresponse()
                    if r.status == 200:
                        age = r.getheader('Age', None)
                        if age:
                            print '  Age: %s seconds (%s)' % (age, timedelta(seconds=int(age)))
                        warning = r.getheader('Warning', None)
                        if warning:
                            print '  Warning: %s' % warning
                    else:
                        print "-- Got HTTP status code %s attempting to get cache age for %s" % (r.status, pdf_url)
                        # re-create connection to avoid getting into a weird state
                        connection.close()
                        #connection = httplib.HTTPConnection(settings.PROXY_HOST)
            elif code == ICP_MISS:
                miss += 1
            # ignoring other codes for now            
            count += 1
            if options['max'] and count >= options['max']:
                break

        # summary
        print "%d document%s of %d cached - %.01f%%" % \
                (hit, 's' if hit != 1 else '', count, float(hit)/float(count)*100.0)
        if hit+miss != count:
            # if hit + miss doesn't account for everything, report numbers
            print "%d hit(s), %d miss(es), %d other" % (hit, miss, count - (hit + miss))

def icp_response_info(datagram):
    # pull ICP response code & request # from response data; logic based on icp.format_datagram
    header_size = struct.calcsize(icp.HEADER_LAYOUT)
    parts = list(struct.unpack(icp.HEADER_LAYOUT, datagram[:header_size]))
    return icp.reverse_opcode_map[parts[0]], parts[3]

