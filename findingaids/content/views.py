import feedparser

from django.shortcuts import render_to_response
from django.template import RequestContext

from findingaids.content.models import BannerFeed
from findingaids.fa.models import title_letters

def site_index(request):
    "Site home page.  Currently includes browse letter links."
    # get banner feed items for rotating home page banner image
    banner = BannerFeed()
    return render_to_response('content/site_index.html', {
                'letters': title_letters(),
                'banner': banner.items,
            }, context_instance=RequestContext(request))

