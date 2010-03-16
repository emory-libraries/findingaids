from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.search.views',
                       (r'^.*$', 'keyword_search')
                       )

