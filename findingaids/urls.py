from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('',
                       # for now, everything is in main app
                       url(r'^$', 'findingaids.fa.views.site_index', name="site-index"),
                       (r'^', include('findingaids.fa.urls')),
)

# DISABLE THIS IN PRODUCTION
if settings.DEV_ENV:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            }),
    )

