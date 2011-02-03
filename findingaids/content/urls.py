from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.content.views',
    url(r'^feedback/$', 'feedback', name="feedback"),
    url(r'^(?P<page>.+)/$', 'content_page', name="page"),
)
