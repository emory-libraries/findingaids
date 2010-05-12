from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',                                                                                  
                       url(r'^admin/', include('findingaids.admin.urls', namespace='admin')),
                       (r'^accounts/login/$', 'django.contrib.auth.views.login'),
                       url(r'^$', 'findingaids.fa.views.site_index', name="site-index"),
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

