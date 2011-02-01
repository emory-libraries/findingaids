from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.content.views',
    url(r'^$', 'site_index', name="index"),
)
