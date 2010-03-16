from django.conf.urls.defaults import *


urlpatterns = patterns('',
                       # for now, everything is in main app
                       (r'^', include('findingaids.fa.urls')),
)
