from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.admin.views',
   url(r'^$', 'main', name="index"),
   url(r'^login$', 'admin_login', name="admin-login"),
   url(r'^logout$', 'admin_logout', name="admin-logout"),
   url(r'^publish$', 'publish', name="publish-ead")
)
