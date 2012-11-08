# file findingaids/urls.py
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
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
   url(r'^robots\.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),
   # embedded url on non-library Emory sites that gets picked up by search bots
   url(r'^-Libraries-EmoryFindingAids$', RedirectView.as_view(url='/', permanent=True)),
                       
   url(r'^db-admin/', include(admin.site.urls)),
   url(r'^admin/', include('findingaids.fa_admin.urls', namespace='fa-admin')),
   url(r'^$', 'findingaids.content.views.site_index', name='site-index'),
   url(r'^content/', include('findingaids.content.urls', namespace='content')),
   # everything else should fall through to the main app
   url(r'^', include('findingaids.fa.urls', namespace='fa')),
)


# DISABLE THIS IN PRODUCTION
if settings.DEV_ENV:
    import os
    # if there's not a genlib_media dir/link in the media directory, then
    # look for it in the virtualenv themes.
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'genlib_media')) and \
            'VIRTUAL_ENV' in os.environ:
        genlib_media_root = os.path.join(os.environ['VIRTUAL_ENV'],
                                         'themes', 'genlib', 'genlib_media')
        urlpatterns += patterns('',
            (r'^static/genlib_media/(?P<path>.*)$', 'django.views.static.serve', {
                'document_root': genlib_media_root,
                }),
        )

    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            }),
    )

