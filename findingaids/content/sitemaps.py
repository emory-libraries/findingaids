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

from datetime import datetime
from time import mktime

from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse


from findingaids.content.models import ContentFeed

# simple object to wrap around feed-based content and local
# django content pages
class ContentPage(object):

    def __init__(self, url):
        self.url = url

    def get_absolute_url(self):
        return self.url


class ContentSitemap(Sitemap):
    changefreq = 'yearly'    # this content changes very rarely

    def items(self):
        items = []

        # collect all content pages via content RSS feed
        for entry_id, entry in ContentFeed().get_items().iteritems():
            items.append(ContentPage(
                url=reverse('content:page', kwargs={'page': entry_id})
            ))
            # NOTE: feed entry includes publication date, but this
            # is probably different from modification date

        # two special cases (non-feed content pages)
        items.extend([
            ContentPage(reverse('content:request-materials')),
            ContentPage(reverse('content:feedback')),
        ])

        return items


