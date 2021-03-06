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
import urllib
import urllib2
import json

from django.contrib import messages
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.template import RequestContext

from findingaids.content.models import BANNER_IMAGES
from findingaids.content.forms import FeedbackForm, RequestMaterialsForm
from findingaids.fa.models import Archive, title_letters
from findingaids.fa.utils import get_findingaid

def site_index(request):
    "Site home page.  Currently includes browse letter links."

    return render(request, 'content/site_index.html', {
                'letters': title_letters(),
                 # images rotating home page banner
                'banner': BANNER_IMAGES,
            })


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
            ''' Begin reCAPTCHA validation '''
            recaptcha_response = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': recaptcha_response
            }
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            result = json.load(response)
            ''' End reCAPTCHA validation '''

            if result['success']:
                try:
                    email_ok = form.send_email()
                    messages.success(request, 'New comment added with success!')
                except Exception as ex:
                    err = ex
                    email_ok = False
                    messages.success(request, 'Invalid reCAPTCHA. Please try again.')
            else:
                email_ok = False
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')

            # display a success/thank you page
            response = render(request, 'content/feedback.html', {
                    'email_sent': email_ok,
                    'err': err,
                })
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

    return render(request, 'content/feedback.html', {
                'form': form,
                'findingaid': ead,
                'captcha_theme': captcha_theme,
            })


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
            response = render(request, 'content/request-materials.html', {
                    'email_sent': email_ok,
                    'err': err,
                })
            # if the email didn't go through, don't return a 200 ok status
            if not email_ok:
                response.status_code = 500
            return response

    else:
        form = RequestMaterialsForm()

    captcha_theme = getattr(settings, 'RECAPTCHA_THEME', None)

    # Filter to remove archives whose contacts include members without an email (null) or with an empty email field
    archives = Archive.objects.filter(contacts__email__isnull=False).exclude(contacts__email__exact='').distinct().order_by("name")

    return render(request, 'content/request-materials.html', {
            'form': form,
            'captcha_theme': captcha_theme,
            'archives': archives
        })
