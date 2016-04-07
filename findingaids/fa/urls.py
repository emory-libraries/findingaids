# file findingaids/fa/urls.py
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
# from django.views.generic.base import RedirectView
from findingaids.fa import views as fa_views


TITLE_LETTERS = '[a-zA-Z]'

title_urlpatterns = [
    url('^$', fa_views.browse_titles, name='browse-titles'),
    url(r'^(?P<letter>%s)/$' % TITLE_LETTERS, fa_views.titles_by_letter,
        name='titles-by-letter'),
    url(r'^xml/$', fa_views.xml_titles, name='all-xml')
]

# patterns for ead document id and series id
# defined here for use in urls and in custom management commands that check id patterns
EADID_URL_REGEX = "(?P<id>[-_A-Za-z0-9.]+)"
series_id = "[a-zA-Z0-9-._]+"

# urls under a single document url (e.g., /documents/abbey244/ )
findingaid_parts = [
    url(r'^$', fa_views.findingaid, name='findingaid'),
    url(r'^EAD/$', fa_views.eadxml, name='eadxml'),
    # TODO: enable this once upgraded to django 1.6+
    # url(r'^ead/$', RedirectView.as_view(pattern_name='fa:eadxml', permanent=True)),

    #Added ead path with a file extension for testing
    url(r'^ead.xml$', fa_views.eadxml, name='eadxml-with-extension'),

    # full finding aid as simple html (html version of pdf, for testing)
    url(r'^full/$', fa_views.full_findingaid,
        {'mode': 'html'}, name='full-findingaid'),
    # view access to XSL-FO used to generate pdf (for testing)
    url(r'^xsl-fo/$', fa_views.full_findingaid,
        {'mode': 'xsl-fo'}, name='xslfo'),
    url(r'^printable/$', fa_views.full_findingaid,
        {'mode': 'pdf'}, name='printable'),
    url(r'^items/$', fa_views.document_search, name='singledoc-search'),
    url(r'^(?P<series_id>%s)/$' % series_id, fa_views.series_or_index,
        name='series-or-index'),
    # NOTE: django can't reverse url patterns with optional parameters
    # so series, subseries, and sub-subseries urls have to be defined separately
    url(r'^(?P<series_id>%(re)s)/(?P<series2_id>%(re)s)/$' % {'re': series_id},
        fa_views.series_or_index, name='series2'),
    url(r'^(?P<series_id>%(re)s)/(?P<series2_id>%(re)s)/(?P<series3_id>%(re)s)/$'
        % {'re': series_id}, fa_views.series_or_index, name='series3'),
]

findingaid_urlpatterns = [
    url(r'^%s/' % EADID_URL_REGEX, include(findingaid_parts)),
]

urlpatterns = [
    url(r'^titles/', include(title_urlpatterns)),
    url(r'^documents/', include(findingaid_urlpatterns)),
    url(r'^search/', fa_views.search, name='search')
]
