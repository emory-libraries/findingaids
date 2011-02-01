from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
   (r'^db-admin/', include(admin.site.urls)),
   url(r'^admin/', include('findingaids.fa_admin.urls', namespace='fa-admin')),
   url(r'^$', 'findingaids.content.views.site_index', name='site-index'),
   url(r'^content/', include('findingaids.content.urls', namespace='content')),
   # everything else should fall through to the main app
   url(r'^', include('findingaids.fa.urls', namespace='fa')),
)

# DISABLE THIS IN PRODUCTION
if settings.DEV_ENV:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            }),
    )

