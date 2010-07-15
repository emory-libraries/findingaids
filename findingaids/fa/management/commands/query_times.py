from datetime import datetime, timedelta
from optparse import make_option


from django.core.management.base import BaseCommand, CommandError
from django.test import Client

from findingaids.fa.models import FindingAid, title_letters
from findingaids.fa.views import fa_listfields

class Command(BaseCommand):
    """Benchmark response times for running queries against the configured eXist
database, and warn if any take longer than the current threshold of 5 seconds.

In browse mode, tests eXist Finding Aid browse query for all browse letters.
"""
    help = __doc__

    _args = ['browse'] # TODO:  search
    args = ' | '.join(_args)
    option_list = BaseCommand.option_list + (
        make_option('--pages', '-p',
            action='store_true',
            dest='pages_only',
            help='Only test page load times'),
        make_option('--xqueries', '-q',
            action='store_true',
            dest='xquery_only',
            help='Only test xquery times'),
        make_option('--url', '-u',
            action='store',
            dest='url',
            help='Base url - required for testing page load times'),
        )

    threshold = 5000
    "warning-level threshold, in ms (queries that take longer than this will generate warnings)"
    timedelta_threshold = timedelta(milliseconds=threshold)
    

    def handle(self, cmd, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        v_all = 2

        url = options['url']

        if cmd not in self._args:
            print "Command '%s' not recognized\n" % cmd
            print self.help
            return

        try:

            # BROWSE
            if cmd == 'browse':
                first_letters = title_letters()
                
                if not options['pages_only']:
                    if verbosity == v_all:
                        print 'Testing response times for browse xqueries'
                        
                    query_times = {}
                    # eXist query times only (without page rendering / content returned)                    
                    for letter in first_letters:
                        # same query used in browse view
                        fa = FindingAid.objects.filter(list_title__startswith=letter).order_by('list_title').only(*fa_listfields)
                        time, total = fa.queryTime(), fa.count()
                        query_times[letter] = time
                        if verbosity >= v_normal:
                            print '%s : %dms, %d records' % (letter, time, total)
                        if fa.queryTime() > self.threshold:
                            print "Warning: query for %s took %dms and returned %d records" % \
                                (letter, time, total)

                    max_min_avg(query_times.values())

                if not options['xquery_only']:
                    if verbosity == v_all:
                        print 'Testing response times for browse pages'

                    client = Client()
                    query_times = {}
                    for letter in first_letters:
                        start_time = datetime.now()
                        # FIXME: how to test non-first pages?
                        uri = "%s/titles/%s" % (url.rstrip('/'), letter)
                        client.get(uri)     # do we need response for any reason ?
                        end_time = datetime.now()
                        duration = end_time - start_time
                        query_times[letter] = duration
                        if duration > self.timedelta_threshold:
                            print "Warning: page load for %s (%s) took %s" % \
                                (letter, uri, duration)
                        if verbosity == v_all:
                            print "%s : %s" % (letter, duration)
                        
                    max_min_avg(query_times.values(), zero=timedelta())
                    

        except Exception, err:
            raise CommandError(err)


def max_min_avg(times, zero=0):
    # calculate and display max/min/average
    max = zero
    min = None
    sum = zero
    for time in times:
        if time > max:
            max = time
        if min is None or time < min:
            min = time
        sum += time
    avg = sum / len(times)
    
    print "Longest time: %s" % max
    print "Shortest time: %s" % min
    print "Average time: %s\n" % avg