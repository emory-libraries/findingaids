from django.conf.urls.defaults import *


urlpatterns = patterns('',
                       # for now, send everything to main fa module
                       (r'^search/', include('findingaids.search.urls')),
                       (r'^', include('findingaids.fa.urls')),
)
