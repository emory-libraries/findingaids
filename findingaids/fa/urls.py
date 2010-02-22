from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.fa.views',
                       (r'^titles/?$', 'browse_titles'),
                       (r'^titles/(?P<letter>[A-Z])$', 'titles_by_letter'),
                       (r'^documents/(?P<id>[a-z0-9-.]+)$', 'view_fa'),
                       (r'^documents/(?P<id>[a-z0-9-.]+)/(?P<series_id>[a-zA-Z0-9._]+)$', 'view_series'),
                       (r'^documents/(?P<id>[a-z0-9-.]+)/(?P<series_id>[a-zA-Z0-9._]+)/(?P<subseries_id>[a-zA-Z0-9._]+)$',
                        	'view_subseries'),
)
 
