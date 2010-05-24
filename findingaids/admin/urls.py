from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.admin.views',
   url(r'^$', 'main', name="index"),
   url(r'^accounts/$', 'admin_list_staff', name="admin-list-staff"),
   url(r'^accounts/user/[0-9.]+/$', 'admin_accounts', name="admin-accounts"),
   url(r'^logout$', 'admin_logout', name="admin-logout"),
   url(r'^publish$', 'publish', name="publish-ead"),
   url(r'^clean/(?P<filename>.*)$', 'clean', name="clean-ead"),
)
