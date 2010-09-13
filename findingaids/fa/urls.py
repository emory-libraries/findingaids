from django.conf.urls.defaults import *

TITLE_LETTERS = '[a-zA-Z]'

title_urlpatterns = patterns('findingaids.fa.views',
    url('^$', 'browse_titles', name='browse-titles'),
    url(r'^(?P<letter>%s)$' % TITLE_LETTERS, 'titles_by_letter', name='titles-by-letter')
)

# patterns for ead document id and series id
# defined here for use in urls and in custom management commands that check id patterns
EADID_URL_REGEX = "(?P<id>[-_A-Za-z0-9.]+)"
series_id = "[a-zA-Z0-9-._]+"

# urls under a single document url (e.g., /documents/abbey244/ )
findingaid_parts = patterns('findingaids.fa.views',
    url(r'^$', 'findingaid', name='findingaid'),
    url(r'^EAD/$', 'eadxml', name='eadxml'),
    url(r'^full/$', 'full_findingaid', {'mode': 'html'}, name='full-findingaid'),     # html version of pdf, for testing
    url(r'^printable/$', 'full_findingaid', {'mode': 'pdf'}, name='printable'),
    url(r'^search/$', 'document_search', name='singledoc-search'),
    url(r'^(?P<series_id>%s)/$' % series_id, 'series_or_index', name='series-or-index'),
    # django can't reverse url patterns with optional parameters
    # so series, subseries, and sub-subseries urls have to be defined separately
    url(r'^(?P<series_id>%(re)s)/(?P<series2_id>%(re)s)/$' % {'re': series_id},
        'series_or_index', name='series2'),
    url(r'^(?P<series_id>%(re)s)/(?P<series2_id>%(re)s)/(?P<series3_id>%(re)s)/$' \
        % {'re': series_id}, 'series_or_index', name='series3'),
)

findingaid_urlpatterns = patterns('findingaids.fa.views',
    (r'^%s/' % EADID_URL_REGEX, include(findingaid_parts)),
)

urlpatterns = patterns('findingaids.fa.views',
    (r'^titles/', include(title_urlpatterns)),
    (r'^documents/', include(findingaid_urlpatterns)),
    url(r'^search/?', 'keyword_search', name='keyword-search')
)
