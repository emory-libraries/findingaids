from django.conf.urls.defaults import *

TITLE_LETTERS = '[a-zA-Z]'

title_urlpatterns = patterns('findingaids.fa.views',
    url('^$', 'browse_titles', name='browse-titles'),
    url(r'^(?P<letter>%s)$' % TITLE_LETTERS, 'titles_by_letter', name='titles-by-letter')    
)

# patterns for ead document id and series id (used in multiple urls)
EADID_URL_REGEX = "(?P<id>[-_A-Za-z0-9.]+)"
series_id = "[a-zA-Z0-9-._]+"

# make document url patterns available in a way that they can be re-used for
# the admin preview urls
def document_urls(**extra_opts):
    return patterns('findingaids.fa.views',
        url(r'^%s/$' % EADID_URL_REGEX, 'view_fa', extra_opts, name='view-fa'),
        url(r'^%s/EAD/$' % EADID_URL_REGEX, 'xml_fa', extra_opts, name='xml-fa'),     # XML content
        url(r'^%s/full/$' % EADID_URL_REGEX, 'full_fa', dict({'mode': 'html'}, **extra_opts),
            name='full-fa'),     # html version of pdf, for testing
        url(r'^%s/printable/$' % EADID_URL_REGEX, 'full_fa', dict({'mode': 'pdf'}, **extra_opts),
            name='printable-fa'),
        url(r'^%s/search/$' % EADID_URL_REGEX, 'document_search', extra_opts, name='singledoc-search'),
        url(r'^%s/(?P<series_id>%s)/$' % (EADID_URL_REGEX, series_id), 'series_or_index',
            extra_opts, name='series-or-index'),
        url(r'^%s/(?P<series_id>%s)/(?P<subseries_id>%s)/$' % \
            (EADID_URL_REGEX, series_id, series_id), 'view_subseries',
            extra_opts, name='view-subseries'),
        url(r'^%s/(?P<series_id>%s)/(?P<subseries_id>%s)/(?P<subsubseries_id>%s)/$' % \
            (EADID_URL_REGEX, series_id, series_id, series_id), 
            'view_subsubseries', extra_opts, name='view-subsubseries')
    )

urlpatterns = patterns('findingaids.fa.views',
    (r'^titles/', include(title_urlpatterns)),
    (r'^documents/', include(document_urls())),
    url(r'^search/?', 'keyword_search', name='keyword-search')
)
