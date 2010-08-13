import httplib
from optparse import make_option

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
        if not hasattr(settings, 'EXISTDB_ROOT_COLLECTION') or not settings.EXISTDB_ROOT_COLLECTION:
            raise CommandError('EXISTDB_ROOT_COLLECTION setting is missing')
            return
        if not hasattr(settings, 'PROXY_HOST') or not settings.PROXY_HOST:
            raise CommandError('PROXY_HOST setting is missing')
            return
        if not hasattr(settings, 'SITE_BASE_URL'):  # could be empty
            raise CommandError('SITE_BASE_URL setting is missing')
            return

        if verbosity >= v_normal:
            print "Checking PDF cache status ",  \
                    '- stopping after %d' % options['max'] if options['max'] else ''
            if verbosity > v_normal:
                print "Proxy URL:\t'%s'" % settings.PROXY_HOST
                print "Site base URL:\t'%s'" % settings.SITE_BASE_URL

        connection = httplib.HTTPConnection(settings.PROXY_HOST)

        count = 0
        hit = 0
        findingaids = FindingAid.objects.all()

        for ead in findingaids:
            url = "%s%s" % (settings.SITE_BASE_URL.rstrip('/'),
                            reverse('fa:printable-fa', kwargs={'id': ead.eadid.value }))
            connection.request('GET', url)
            r = connection.getresponse()
            cached = r.getheader('X-Cache').startswith('HIT')
            age = r.getheader('Age', None)
            warning = r.getheader('Warning', None)
            if verbosity > v_normal or (verbosity == v_normal and warning is not None):
                info = ["%28s : %10s" % (ead.eadid.value, 'cached' if cached else 'not cached')]
                if age:
                    info.append('age: %s' % age)
                if warning:
                    info.append('warning: %s' % warning)
                print '\t'.join(info)

            if cached:
                hit += 1
            
            count += 1
            if options['max'] and count >= options['max']:
                break
                
        # summary
        print "Checked %d document%s - %.01f%% cached" % \
                (count, 's' if count != 1 else '', float(hit)/float(count)*100.0)
        print "%d document%s cached" % (hit, 's' if hit != 1 else '')
