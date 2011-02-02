from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.content.views',
    url(r'^(?P<page>.+)/$', 'content_page', name="page"),
)
