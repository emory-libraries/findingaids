# file findingaids/fa_admin/urls.py
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
from findingaids.fa.urls import EADID_URL_REGEX, findingaid_urlpatterns

urlpatterns = patterns('findingaids.fa_admin.views',
    url(r'^$', 'main', name="index"),
    url(r'^files/(?P<archive_id>[a-z0-9]+)/', 'list_files', name='files'),
    url(r'^accounts/$', 'list_staff', name="list-staff"),
    url(r'^accounts/logout$', 'logout', name="logout"),
    url(r'^publish/$', 'publish', name="publish-ead"),
    url(r'^preview/$', 'preview', name="preview-ead"),
    url(r'^(?P<filename>[^/]+)/prep/$', 'prepared_eadxml', name="prep-ead"),
    url(r'^(?P<filename>[^/]+)/prep/diff/', 'prepared_ead', {'mode': 'diff'},
            name="prep-ead-diff"),
    url(r'^(?P<filename>[^/]+)/prep/about/', 'prepared_ead', {'mode': 'summary'},
            name="prep-ead-about"),
    # include finding aid document urls in preview mode
    url(r'^preview/documents/', include(findingaid_urlpatterns, namespace='preview'),
            {'preview': True}),
    url(r'^documents/$', 'list_published', name="list-published"),
    url(r'^documents/%s/delete/$' % EADID_URL_REGEX, 'delete_ead', name="delete-ead"),
)

# contrib views
urlpatterns += patterns('django.contrib.auth.views',
    url(r'^accounts/login/$', 'login', name='login'),
    # note: could use contrib logout; custom view simply adds a message
    #url(r'^accounts/logout$', 'logout_then_login', name="logout"),
)

