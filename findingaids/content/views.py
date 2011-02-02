import feedparser

from django.shortcuts import render_to_response
from django.template import RequestContext

from findingaids.content.models import BannerFeed, NewsFeed
from findingaids.fa.models import title_letters

def site_index(request):
    "Site home page.  Currently includes browse letter links."

   # announcements - if any, pass the first (most recent) for display
    newsfeed = NewsFeed()
    if newsfeed.items:
        news = newsfeed.items[0]
    else:
        news = None

    return render_to_response('content/site_index.html', {
                'letters': title_letters(),
                 # banner feed items for rotating home page banner image
                'banner': BannerFeed().items,
                'news': news,
            }, context_instance=RequestContext(request))

