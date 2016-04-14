from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from findingaids.fa_admin import views
from findingaids.fa_admin.models import Archivist


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class ArchivistInline(admin.StackedInline):
    model = Archivist
    can_delete = False
    verbose_name_plural = 'archivist'
    fields = ('archives', )


# Customize user admin to include archivist information
class ArchivistUserAdmin(UserAdmin):
    inlines = (ArchivistInline, )
    list_filter = ('archivist__archives', 'is_staff', 'is_superuser',
                   'is_active', 'groups')

    def get_urls(self):
        return [
            url(r'ldap-user/$', views.init_ldap_user, name='init-ldap-user')
        ] + super(ArchivistUserAdmin, self).get_urls()


# Re-register UserAdmin
admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), ArchivistUserAdmin)