#from datetime import datetime

from django.core.management.base import BaseCommand #, CommandError
#from django.test import Client

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

    threshold = 5000
    "warning-level threshold, in ms (queries that take longer than this will generate warnings)"

    def handle(self, cmd, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        v_all = 2

        if cmd not in self._args:
            print "Command '%s' not recognized\n" % cmd
            print self.help
            return

        # BROWSE
        if cmd == 'browse':
            if verbosity == v_all:
                print 'Testing response times for browse queries'
            query_times = {}
            # eXist query times only (without page rendering / content returned)
            first_letters = title_letters()
            query_times['browse letters'] = first_letters.queryTime()
            for letter in first_letters:
                # same query used in browse view
                fa = FindingAid.objects.filter(list_title__startswith=letter).order_by('list_title').only(*fa_listfields)
                time, total = fa.queryTime(), fa.count()
                query_times[letter] = time
                if verbosity == v_all:
                    print '%s : %dms, %d records' % (letter, time, total)
                if fa.queryTime() > self.threshold:
                    print "Warning: query for %s took %dms and returned %d records" % \
                        (letter, time, total, self.threshold)

            # calculate max/min/average
            max = 0
            min = 10000
            sum = 0
            for time in query_times.values():
                if time > max:
                    max = time
                if time < min:
                    min = time
                sum += time
            avg = sum / len(query_times)
            if verbosity >= v_normal:
                print "Longest time: %dms" % max
                print "Shortest time: %dms" % min
                print "Average time: %dms" % avg