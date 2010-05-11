from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.admin.views',
   url(r'^$', 'main', name="index"),
   url(r'^login$', 'admin_login', name="admin-login"),
   url(r'^publish$', 'publish', name="publish-ead")
)
