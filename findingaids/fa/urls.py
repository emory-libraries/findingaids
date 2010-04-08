from django.conf.urls.defaults import *


title_urlpatterns = patterns('findingaids.fa.views',
    ('^$', 'browse_titles'),
    (r'^(?P<letter>[A-Z])$', 'titles_by_letter')
)

# patterns for ead document id and series id (used in multiple urls)
ead_id = "(?P<id>[A-Za-z0-9-.]+)"
series_id = "[a-zA-Z0-9-._]+"

document_urlpatterns = patterns('findingaids.fa.views',
    (r'^%s$' % ead_id, 'view_fa'),
    (r'^%s/full$' % ead_id, 'full_fa', {'mode' : 'html'}),     # html version of pdf, for testing
    (r'^%s/printable$' % ead_id, 'full_fa', {'mode' : 'pdf'}, 'printable-fa'),
    (r'^%s/(?P<series_id>%s)$' % (ead_id, series_id), 'view_series'),
    (r'^%s/(?P<series_id>%s)/(?P<subseries_id>%s)$' % (ead_id, series_id, series_id),
        'view_subseries'),
    (r'^%s/(?P<series_id>%s)/(?P<subseries_id>%s)/(?P<subsubseries_id>%s)$' % (ead_id, series_id, series_id, series_id),
        'view_subsubseries')
)

urlpatterns = patterns('findingaids.fa.views',
    (r'^titles/', include(title_urlpatterns)),
    (r'^documents/', include(document_urlpatterns)),
    (r'^search/?', 'keyword_search')
)
