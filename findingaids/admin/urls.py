from django.conf.urls.defaults import *
from findingaids.fa.urls import document_urls

urlpatterns = patterns('findingaids.admin.views',
    url(r'^$', 'main', name="index"),
    url(r'^accounts/$', 'list_staff', name="list-staff"),
    url(r'^accounts/user/(?P<user_id>[0-9.]+)/$', 'edit_user', name="edit-user"),
    url(r'^logout$', 'logout', name="logout"),
    url(r'^publish$', 'publish', name="publish-ead"),
    url(r'^preview$', 'preview', name="preview-ead"),
    url(r'^(?P<filename>[^/]+)/cleaned$', 'cleaned_eadxml', name="cleaned-ead"),
    url(r'^(?P<filename>[^/]+)/cleaned/diff', 'cleaned_ead', {'mode': 'diff'}, name="cleaned-ead-diff"),
    url(r'^(?P<filename>[^/]+)/cleaned/about', 'cleaned_ead', {'mode': 'summary'}, name="cleaned-ead-about"),
    # include finding document urls for preview
    url(r'^preview/documents/', include(document_urls(preview=True), namespace='preview')),
)

