from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.content.views',
    url(r'^request-materials/$', 'request_materials', name="request-materials"),
    url(r'^feedback/$', 'feedback', name="feedback"),
    url(r'^(?P<page>.+)/$', 'content_page', name="page"),
)
