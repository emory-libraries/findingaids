from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from findingaids.content.models import BannerFeed, NewsFeed, ContentFeed
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

def content_page(request, page):
    'Display content based on an item in the configured RSS feed.'
    content = ContentFeed()
    page = content.get_entry(page)
    if page is None:
        raise Http404
    return render_to_response('content/page.html', {
                'page': page,
            }, context_instance=RequestContext(request))
