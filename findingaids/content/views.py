from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from findingaids.content.models import BannerFeed, NewsFeed, ContentFeed
from findingaids.content.forms import FeedbackForm
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

def feedback(request):
    '''Feedback form. On GET, displays the form; on POST, processes the submitted
    form and sends an email (if all required fields are present).'''
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            err = None
            try:
                email_ok = form.send_email()
                # if it processed without exception, email should be sent ok
            except Exception as ex:
                err = ex
                email_ok = False
            # display a success/thank you page
            response = render_to_response('content/feedback.html', {
                    'email_sent': email_ok,
                    'err': err,
                }, context_instance=RequestContext(request))
            # if the email didn't go through, don't return a 200 ok status
            if not email_ok:
                response.status_code = 500
            return response
    else:
        form = FeedbackForm()

    return render_to_response('content/feedback.html', {
                'form': form,
            }, context_instance=RequestContext(request))

