from django.conf.urls.defaults import *
from findingaids.fa.urls import EADID_URL_REGEX, findingaid_urlpatterns

urlpatterns = patterns('findingaids.fa_admin.views',
    url(r'^$', 'main', name="index"),
    url(r'^accounts/$', 'list_staff', name="list-staff"),
    url(r'^accounts/user/(?P<user_id>[0-9.]+)/$', 'edit_user', name="edit-user"),
    url(r'^accounts/logout$', 'logout', name="logout"),
    url(r'^publish$', 'publish', name="publish-ead"),
    url(r'^preview$', 'preview', name="preview-ead"),
    url(r'^(?P<filename>[^/]+)/prep$', 'prepared_eadxml', name="prep-ead"),
    url(r'^(?P<filename>[^/]+)/prep/diff', 'prepared_ead', {'mode': 'diff'},
            name="prep-ead-diff"),
    url(r'^(?P<filename>[^/]+)/prep/about', 'prepared_ead', {'mode': 'summary'},
            name="prep-ead-about"),
    # include finding aid document urls in preview mode
    url(r'^preview/documents/', include(findingaid_urlpatterns, namespace='preview'),
            {'preview': True}),
    url(r'^documents/$', 'list_published', name="list-published"),
    url(r'^documents/%s/delete$' % EADID_URL_REGEX, 'delete_ead', name="delete-ead"),
)

# contrib views 
urlpatterns += patterns('django.contrib.auth.views',
    url(r'^accounts/login/$', 'login', name='login'),
    # note: could use contrib logout; custom view simply adds a message
    #url(r'^accounts/logout$', 'logout_then_login', name="logout"),
)

