
# file findingaids/content/sitemaps.py
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


class ContentSitemap(Sitemap):
    changefreq = 'yearly'    # this content changes very rarely
    default_priority = 0.4   # lower priority than actual findingaid content

    # names for pages within content url namespace
    content_pages = ['request-materials', 'feedback', 'faq',
                     'search-tips', 'contributors']


    def items(self):
        # special case pages - index, static html site pages
        items = [reverse('content:%s' % page) for page in self.content_pages]
        items.append(reverse('site-index'))

        # possibly also advanced search? (not really content to index)

        # generate list of higher priority urls (can't be calculated at load
        # time because urls haven't been defined yet)
        self.higher_priority = [reverse('site-index'), reverse('content:faq'),
                       reverse('content:search-tips')]

        return items

    def location(self, item):
        return item

    def priority(self, item):
        # set specific urls (such as home page) to higher priority
        if item in self.higher_priority:
            return 0.5
        return self.default_priority
