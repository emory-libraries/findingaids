from django.conf.urls.defaults import *

title_urlpatterns = patterns('findingaids.fa.views',
    url('^$', 'browse_titles', name='browse-titles'),
    url(r'^(?P<letter>[A-Z])$', 'titles_by_letter', name='titles-by-letter')
)

# patterns for ead document id and series id (used in multiple urls)
EADID_URL_REGEX = "(?P<id>[-_A-Za-z0-9.]+)"
series_id = "[a-zA-Z0-9-._]+"

document_urlpatterns = patterns('findingaids.fa.views',
    url(r'^%s$' % EADID_URL_REGEX, 'view_fa', name='view-fa'),
    url(r'^%s/full$' % EADID_URL_REGEX, 'full_fa', {'mode' : 'html'}, name='full-fa'),     # html version of pdf, for testing
    url(r'^%s/printable$' % EADID_URL_REGEX, 'full_fa', {'mode' : 'pdf'}, name='printable-fa'),
    url(r'^%s/(?P<series_id>%s)$' % (EADID_URL_REGEX, series_id), 'series_or_index', name='series-or-index'),
    url(r'^%s/(?P<series_id>%s)/(?P<subseries_id>%s)$' % (EADID_URL_REGEX, series_id, series_id),
        'view_subseries', name='view-subseries'),
    url(r'^%s/(?P<series_id>%s)/(?P<subseries_id>%s)/(?P<subsubseries_id>%s)$' % (EADID_URL_REGEX, series_id, series_id, series_id),
        'view_subsubseries', name='view-subsubseries')
)

urlpatterns = patterns('findingaids.fa.views',
    (r'^titles/', include(title_urlpatterns)),
    (r'^documents/', include(document_urlpatterns)),
    url(r'^search/?', 'keyword_search', name='keyword-search')
)
