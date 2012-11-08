# file findingaids/fa/management/commands/response_times.py
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

from datetime import datetime, timedelta
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.test import Client

from findingaids.fa.models import FindingAid, title_letters
from findingaids.fa.views import fa_listfields

class Command(BaseCommand):
    """
    Benchmark response times for running queries against the configured eXist
    database, and warn if any take longer than the current threshold of 5 seconds.

    In browse mode, tests eXist Finding Aid browse query for all browse letters.
    
    """
    help = __doc__

    _args = ['browse', 'search']
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
        )

    threshold = 5000
    "warning-level threshold, in ms (queries that take longer than this will generate warnings)"
    timedelta_threshold = timedelta(milliseconds=threshold)

    # sample searches to use for testing search response times
    test_searches = (
        'African American*',
        '(Oral histor*) AND Atlanta',
        'World War I',
        '''Flannery O'Connor''',
        'Segregat* +Georgia',
        '"New York Times" AND journalis*',
    )

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
            first_letters = title_letters()

            if not options['pages_only']:
                # get eXist query times without page load
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
                    current_times = {}  # times for the current letter
                    uri = "/titles/%s" % letter     # FIXME: use reverse here
                    if verbosity == v_all:
                        print letter
                    for page in range(1,11):
                        start_time = datetime.now()
                        response = client.get(uri, {'page': page})
                        end_time = datetime.now()
                        if response.status_code == 200:
                            duration = end_time - start_time                            
                            current_times['%s %d' % (letter, page)] = duration
                            if duration > self.timedelta_threshold:
                                print "Warning: page load for page %d of %s (%s) took %s" % \
                                    (page, letter, uri, duration)
                            if verbosity == v_all:
                                print "  page %d : %s" % (page, duration)

                    if verbosity >= v_normal and len(current_times) > 1:
                        # summarize times for current letter
                        print "\nMax/Min/Average for %s (all pages)" % letter
                        max_min_avg(current_times.values(), zero=timedelta())
                    # add times for current letter to all query times
                    query_times.update(current_times)

                print "\nMax/Min/Average - all letters, all pages"
                max_min_avg(query_times.values(), zero=timedelta())

        # SEARCH
        elif cmd == 'search':
            client = Client()
            query_times = {}

            if not options['pages_only']:
                # get eXist query times without page load
                if verbosity == v_all:
                    print 'Testing response times for search xqueries'                
                for search_terms in self.test_searches:
                    # NOTE: search syntax duplicated from search view
                    search_fields = fa_listfields
                    search_fields.append('fulltext_score')
                    fa = FindingAid.objects.filter(fulltext_terms=search_terms).or_filter(
                        fulltext_terms=search_terms,
                        boostfields__fulltext_terms=search_terms,
                    ).order_by('-fulltext_score').only(*search_fields)

                    time, total = fa.queryTime(), fa.count()
                    query_times[search_terms] = time
                    if verbosity >= v_normal:
                        print '%s : %dms, %d records' % (search_terms, time, total)
                    if fa.queryTime() > self.threshold:
                        print "Warning: query for %s took %dms and returned %d records" % \
                            (letter, time, total)

                print "\nMax/Min/Average - search queries, eXist response time"
                max_min_avg(query_times.values())

            if not options['xquery_only']:
                if verbosity == v_all:
                    print 'Testing response times for search pages'

                query_times = {}
                for search_terms in self.test_searches:
                    current_times = {}  # times for the current search
                    uri = reverse('fa:search')
                    if verbosity == v_all:
                        print search_terms
                    for page in range(1,11):
                        start_time = datetime.now()
                        response = client.get(uri, {'page': page, 'keywords': search_terms})
                        end_time = datetime.now()
                        if response.status_code == 200:
                            duration = end_time - start_time
                            current_times['%s %d' % (search_terms, page)] = duration
                            if duration > self.timedelta_threshold:
                                print "Warning: page load for page %d of %s (%s) took %s" % \
                                    (page, search_terms, uri, duration)
                            if verbosity == v_all:
                                print "  page %d : %s" % (page, duration)


                    # summarize times for current search
                    print "\nMax/Min/Average for %s (all pages)" % search_terms
                    max_min_avg(current_times.values(), zero=timedelta())
                    # add times for current letter to all query times
                    query_times.update(current_times)

                print "\nMax/Min/Average - all letters, all pages"
                max_min_avg(query_times.values(), zero=timedelta())

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