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

from findingaids.content.models import ContentFeed


class ContentPage(object):
# simple object to wrap around feed-based content and local
# django content pages

    def __init__(self, url):
        self.url = url

    def get_absolute_url(self):
        return self.url


class ContentSitemap(Sitemap):
    changefreq = 'yearly'    # this content changes very rarely
    default_priority = 0.4   # lower priority than actual findingaid content

    def items(self):
        # special case pages
        # non-findingaid site pages not based on feed content
        items = [
            ContentPage(reverse('site-index')),
            ContentPage(reverse('content:request-materials')),
            ContentPage(reverse('content:feedback')),
            # possibly also advanced search? (not really content to index)
        ]

        # collect all content pages via content RSS feed
        # NOTE: feed entry includes publication date, but it is not
        # included here because we can't rely on publication
        # date being the same as last modification date
        for entry_id, entry in ContentFeed().get_items().iteritems():
            items.append(ContentPage(
                url=reverse('content:page', kwargs={'page': entry_id})
            ))

        return items

    def priority(self, item):
        # set home page to higher priority
        # NOTE: faq and search tips might also possibly be higher
        # priority than other pages
        if item.get_absolute_url() == reverse('site-index'):
            return 0.5
        return self.default_priority
