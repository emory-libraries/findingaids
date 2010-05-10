from django.conf.urls.defaults import *

urlpatterns = patterns('findingaids.admin.views',
   url(r'^$', 'admin_login', name="admin-login")
)
