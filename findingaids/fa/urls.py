from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.fa.views',
                       (r'^browse/$', 'browse'),
                       (r'^browse/(?P<letter>[A-Z])$', 'browse_by_letter'),
                       (r'^view/(?P<id>.*)$', 'view_fa'),
)
 
