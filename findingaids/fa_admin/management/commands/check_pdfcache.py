import httplib
from optparse import make_option
import socket
from socket import timeout
import struct
from zc import icp

from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.conf import settings


from findingaids.fa.models import FindingAid

class Command(BaseCommand):
    """Check status of Finding Aid PDFs in the configured cache."""
    help = __doc__

    args = '[<filename filename ... >]'

    option_list = BaseCommand.option_list + (
        make_option('--max', '-m',
            dest='max',
            type='int',
            help='Test only the specified number of PDFs (by default, checks all)'),
        )

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1

        # check for required settings
        if not hasattr(settings, 'PROXY_HOST'):
            raise CommandError('PROXY_HOST setting is missing')
            return
        if not hasattr(settings, 'SITE_BASE_URL'):  # could be empty
            raise CommandError('SITE_BASE_URL setting is missing')
            return

        if verbosity >= v_normal:
            print "Checking status of printable Finding Aid in configured cache",  \
                    '- stopping after %d' % options['max'] if options['max'] else ''
 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((settings.PROXY_HOST, settings.PROXY_ICP_PORT))
        
        count = 0
        hit = 0
        miss = 0
        result_fmt = '%(eadid)30s%(status)15s'
        findingaids = FindingAid.objects.all()

        for ead in findingaids:
            # url to query the cache for - must be null-terminated
            url = "%s%s\0" % (settings.SITE_BASE_URL.rstrip('/'),
                            reverse('fa:printable-fa', kwargs={'id': ead.eadid.value }))
            query = icp.HEADER_LAYOUT + icp.QUERY_LAYOUT
            format = query % len(url)
            icp_request = struct.pack(
                format, 1, 2, struct.calcsize(format), 0xDEADBEEF, 0, 0, 0, 0, url)
            # TODO: use count for request # instead of DEADBEEF ?
            s.send(icp_request)
            icp_response = s.recv(16384)
            #print icp.format_datagram(icp_response)
            code = icp_response_code(icp_response)
            # if ICP is denied, error and bail out
            if code in ('ICP_OP_DENIED', 'ICP_OP_ERR'):
                print "Error: got response code %s -- check that proxy is configured to allow ICP queries" % code
                return
            
            if verbosity > v_normal:
                print result_fmt % {'eadid': ead.eadid.value, 'status': code}
            if code == 'ICP_OP_HIT':
                hit += 1
            elif code == 'ICP_OP_MISS':
                miss += 1
            # any other code - ignore for now (maybe check for DENIED?)
            
            count += 1
            if options['max'] and count >= options['max']:
                break

        # summary
        print "%d document%s of %d cached - %.01f%%" % \
                (hit, 's' if hit != 1 else '', count, float(hit)/float(count)*100.0)
        if hit+miss != count:
            # if hit + miss doesn't account for everything, report numbers
            print "%d hit(s), %d miss(es), %d other" % (hit, miss, count - (hit + miss))

def icp_response_code(datagram):
    # pull ICP response code out from response data; logic based on icp.format_datagram 
    header_size = struct.calcsize(icp.HEADER_LAYOUT)
    parts = list(struct.unpack(icp.HEADER_LAYOUT, datagram[:header_size]))
    return icp.reverse_opcode_map[parts[0]]

