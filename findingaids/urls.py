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

from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from findingaids.fa.sitemaps import FINDINGAID_SITEMAPS
from findingaids.content.sitemaps import ContentSitemap

admin.autodiscover()

urlpatterns = [
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt',
        content_type='text/plain')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/favicon.ico',
        permanent=True)),

    # embedded url on non-library Emory sites that gets picked up by search bots
    url(r'^-Libraries-EmoryFindingAids$',
        RedirectView.as_view(url='/', permanent=True)),

    url(r'^db-admin/', include(admin.site.urls)),
    url(r'^admin/', include('findingaids.fa_admin.urls',
                            namespace='fa-admin')),
    url(r'^$', 'findingaids.content.views.site_index',
        name='site-index'),
    url(r'^content/', include('findingaids.content.urls',
                              namespace='content')),
    # everything else should fall through to the main app
    url(r'^', include('findingaids.fa.urls', namespace='fa')),
]

# xml sitemaps for search-engine discovery
sitemap_cfg = {'content': ContentSitemap}
sitemap_cfg.update(FINDINGAID_SITEMAPS)

urlpatterns += [
    url(r'^sitemap\.xml$', sitemaps_views.index, {'sitemaps': sitemap_cfg},
       name='django.contrib.sitemaps.views.sitemap'),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemaps_views.sitemap,
       {'sitemaps': sitemap_cfg},
       name='django.contrib.sitemaps.views.sitemap'),
]

# enable serving static files for development (DEBUG mode only)
urlpatterns += staticfiles_urlpatterns()
