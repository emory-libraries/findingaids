# file findingaids/fa/sitemaps.py
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

from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from findingaids.fa.models import FindingAid, Series, Series2, \
    Series3, Index


class _BaseFindingAidSitemap(Sitemap):
    # base findingaid sitemap object with common functionality
    priority = 0.5  # default priority
    view_name = ''

    def url_args(self, obj):
        return {}

    def location(self, obj):
        return reverse(self.view_name,
                       kwargs=self.url_args(obj))

    def lastmod(self, obj):
        return obj.last_modified


class FindingAidSitemap(_BaseFindingAidSitemap):
    priority = 0.6  # main findingaid page should be highest priority
    view_name = 'fa:findingaid'

    def items(self):
        return FindingAid.objects.only('eadid', 'last_modified')

    def url_args(self, obj):
        return {'id': obj.eadid}


class PDFSitemap(FindingAidSitemap):
    # same query as findingaids, different url and priority
    priority = 0.5
    view_name = 'fa:printable'


class EADXMLSitemap(FindingAidSitemap):
    # same query as findingaids & PDF, different url and priority
    # Not sure if exposing XML in sitemaps is useful, so setting
    # priority fairly low
    priority = 0.3
    view_name = 'fa:eadxml'


class SeriesSitemap(_BaseFindingAidSitemap):
    # sitemap for findingaid series that are displayed on their
    # own pages
    view_name = 'fa:series-or-index'

    def items(self):
        return Series.objects.filter(level='series') \
            .only('id', 'ead__eadid', 'last_modified')

    def url_args(self, obj):
        return {'id': obj.ead.eadid, 'series_id': obj.short_id}


class IndexSitemap(SeriesSitemap):
    # sitemap for index entry pages, for findingaids that have them
    # same url format as series, different query

    def items(self):
        # FIXME: this filter is a bit of a cheat:
        # what we really want is a not empty/exists, or a not filter
        # (NOTE: indexentry without an id probably shouldn't be loaded,
        # but filter them out to avoid the sitemap breaking for them.)
        return Index.objects.filter(id__contains='_') \
                            .only('id', 'ead__eadid', 'last_modified')


class SubseriesSitemap(_BaseFindingAidSitemap):
    # sitemap for findingaid subseries that are displayed on their
    # own pages

    view_name = 'fa:series2'

    def items(self):
        return Series2.objects.filter(level='subseries') \
            .only('id', 'ead__eadid', 'series__id', 'last_modified')

    def url_args(self, obj):
        return {
            'id': obj.ead.eadid,
            'series_id': obj.series.short_id,
            'series2_id': obj.short_id
        }


class SubsubseriesSitemap(_BaseFindingAidSitemap):
    # same as subseries, but for sub-subseries
    view_name = 'fa:series3'

    def items(self):
        return Series3.objects.filter(level='subseries') \
            .only('id', 'ead__eadid', 'series__id',
                  'series2__id', 'last_modified')

    def url_args(self, obj):
        return {
            'id': obj.ead.eadid,
            'series_id': obj.series.short_id,
            'series2_id': obj.series2.short_id,
            'series3_id': obj.short_id
        }


# dictionary of sitemap objects for use with sitemap views
FINDINGAID_SITEMAPS = {
    'findingaids': FindingAidSitemap,
    'findingaids-pdf': PDFSitemap,
    'findingaids-eadxml': EADXMLSitemap,   # maybe
    'findingaids-series': SeriesSitemap,
    'findingaids-subseries': SubseriesSitemap,
    'findingaids-subsubseries': SubsubseriesSitemap,
    'findingaids-index': IndexSitemap,
}
