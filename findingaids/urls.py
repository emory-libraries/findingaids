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
    import os
    # if there's not a genlib_media dir/link in the media directory, then
    # look for it in the virtualenv themes.
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'genlib_media')) and \
            'VIRTUAL_ENV' in os.environ:
        genlib_media_root = os.path.join(os.environ['VIRTUAL_ENV'],
                                         'themes', 'genlib', 'genlib_media')
        urlpatterns += patterns('',
            (r'^static/genlib_media/(?P<path>.*)$', 'django.views.static.serve', {
                'document_root': genlib_media_root,
                }),
        )

    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            }),
    )

