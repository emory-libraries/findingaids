from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       # for now, everything is in main app
                       (r'^admin/', include('findingaids.admin.urls')),
                       (r'^db-admin/', include(admin.site.urls)),
                       url(r'^$', 'findingaids.fa.views.site_index', name="site-index"),
                       url(r'^', include('findingaids.fa.urls', namespace='fa')),
)

# DISABLE THIS IN PRODUCTION
if settings.DEV_ENV:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            }),
    )

