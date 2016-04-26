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

from django.conf.urls import url, patterns, include
from django.contrib.auth import views as authviews
from findingaids.fa.urls import EADID_URL_REGEX, findingaid_urlpatterns
from findingaids.fa_admin import views

urlpatterns = [
    url(r'^$', views.main, name="index"),
    url(r'^(?P<archive>[a-z0-9-]+)/files/', views.list_files, name='files'),
    url(r'^archives/order/', views.archive_order, name='archive-order'),
    url(r'^archives/current/', views.current_archive, name='current-archive'),
    url(r'^accounts/logout$', views.logout, name="logout"),
    url(r'^publish/$', views.publish, name="publish-ead"),
    url(r'^(?P<archive>[a-z0-9-]+)/preview/$', views.preview, name="preview-ead"),
    url(r'^(?P<archive>[a-z0-9-]+)/(?P<filename>[^/]+)/prep/$',
        views.prepared_eadxml, name="prep-ead"),
    url(r'^(?P<archive>[a-z0-9-]+)/(?P<filename>[^/]+)/prep/diff/',
        views.prepared_ead, {'mode': 'diff'}, name="prep-ead-diff"),
    url(r'^(?P<archive>[a-z0-9-]+)/(?P<filename>[^/]+)/prep/about/',
        views.prepared_ead, {'mode': 'summary'}, name="prep-ead-about"),
    # include finding aid document urls in preview mode
    url(r'^preview/documents/', include(findingaid_urlpatterns, namespace='preview'),
            {'preview': True}),
    url(r'^documents/$', views.list_published, name="list-published"),
    url(r'^(?P<archive>[a-z0-9-]+)/documents/$', views.list_published, name="published-by-archive"),
    url(r'^documents/%s/delete/$' % EADID_URL_REGEX, views.delete_ead, name="delete-ead"),
    url(r'^(?P<archive>[a-z0-9-]+)/documents/%s/delete/$' % EADID_URL_REGEX, views.delete_ead,
        name="delete-ead-by-archive"),

    # contrib auth login
    # note: could use contrib logout; custom view simply adds a message
    url(r'^accounts/login/$', authviews.login, name='login'),
    # url(r'^accounts/logout$', authviews.logout_then_login, name="logout"),
]


