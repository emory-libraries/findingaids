# file findingaids/content/views.py
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

from django.conf import settings
from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from findingaids.content.models import BannerFeed, NewsFeed, ContentFeed
from findingaids.content.forms import FeedbackForm, RequestMaterialsForm
from findingaids.fa.models import title_letters
from findingaids.fa.utils import get_findingaid

def site_index(request):
    "Site home page.  Currently includes browse letter links."

   # announcements - if any, pass the first (most recent) for display
    newsfeed = NewsFeed()
    try:
        news = newsfeed.items[0]
    except IndexError:
        news = None

    return render_to_response('content/site_index.html', {
                'letters': title_letters(),
                 # banner feed items for rotating home page banner image
                'banner': BannerFeed().items,
                'news': news,
                'about': ContentFeed().get_entry('about'),
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
    ead = None
    if request.method == 'POST':
        data = request.POST.copy()
        data['remote_ip'] = request.META['REMOTE_ADDR']
        form = FeedbackForm(data)
        if form.is_valid():
            err = None
            try:
                email_ok = form.send_email()
                # if it processed without exception, email should be sent ok
            except Exception as ex:
                err = ex
                email_ok = False
            # display a success/thank you page
            response = render_to_response ('content/feedback.html', {
                    'email_sent': email_ok,
                    'err': err,
                }, context_instance=RequestContext(request))
            # if the email didn't go through, don't return a 200 ok status
            if not email_ok:
                response.status_code = 500
            return response
    else:
        ead = None
        if 'eadid' in request.GET:
            # retrieve minimal ead info to display ead title to user on the form
            try:
                ead = get_findingaid(eadid=request.GET['eadid'], only=['title'])
            except:
                # if retrieval fails, ignore it - not required for the form to work
                pass

        # GET may include eadid & url; use as initial data to populate those fields
        form = FeedbackForm(initial=request.GET)

    captcha_theme = getattr(settings, 'RECAPTCHA_THEME', None)

    return render_to_response('content/feedback.html', {
                'form': form,
                'findingaid': ead,
                'captcha_theme': captcha_theme,
            }, context_instance=RequestContext(request))

def request_materials(request):
    if request.method == 'POST':
        form = RequestMaterialsForm(request.POST)
        if form.is_valid():
            err = None
            try:
                email_ok = form.send_email()
                # if it processed without exception, email should be sent ok
            except Exception as ex:
                err = ex
                email_ok = False
            # TODO: use separate result page for request materials
            # display a success/thank you page
            response = render_to_response ('content/request-materials.html', {
                    'email_sent': email_ok,
                    'err': err,
                }, context_instance=RequestContext(request))
            # if the email didn't go through, don't return a 200 ok status
            if not email_ok:
                response.status_code = 500
            return response

    else:
        form = RequestMaterialsForm()

    captcha_theme = getattr(settings, 'RECAPTCHA_THEME', None)

    return render_to_response('content/request-materials.html', {
            'form': form,
            'captcha_theme': captcha_theme,
        }, context_instance=RequestContext(request))

