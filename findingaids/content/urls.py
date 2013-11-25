# file findingaids/content/urls.py
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

from django.conf.urls.defaults import *
from django.views.generic import TemplateView


urlpatterns = patterns('findingaids.content.views',
    url(r'^request-materials/$', 'request_materials', name='request-materials'),
    url(r'^feedback/$', 'feedback', name='feedback'),
    url(r'^faq/$', TemplateView.as_view(template_name='content/faq.html'),
        name='faq'),
    url(r'^search-tips/$', TemplateView.as_view(template_name='content/search_tips.html'),
        name='search-tips'),
    url(r'^institutions/$', TemplateView.as_view(template_name='content/contributors.html'),
        name='contributors'),
)
