from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.simplepages.views',
    url(r'^(?P<url>.*)$', 'simplepage', name="viewpage"),
)