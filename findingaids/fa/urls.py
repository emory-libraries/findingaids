from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.fa.views',
                       (r'^browse/?$', 'browse'),
                       (r'^browse/(?P<letter>[A-Z])$', 'browse_by_letter'),
                       (r'^view/(?P<id>[a-z0-9-.]+)$', 'view_fa'),
                       (r'^view/(?P<id>[a-z0-9-.]+)/(?P<series_id>[a-zA-Z0-9._]+)$', 'view_series'),
                       (r'^view/(?P<id>[a-z0-9-.]+)/(?P<series_id>[a-zA-Z0-9._]+)/(?P<subseries_id>[a-zA-Z0-9._]+)$',
                        	'view_subseries'),
)
 
