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


# patch some custom properties onto User for display in admin site
User = get_user_model()


def is_ldap(self):
    return self.password == '!'
is_ldap.short_description = 'LDAP'
is_ldap.boolean = True


def group_list(self):
    return ', '.join(group.name for group in self.groups.all())
group_list.short_description = 'Groups'


def archive_list(self):
    return ', '.join(archive.label for archive in self.archivist.archives.all())
archive_list.short_description = 'Archives'

User.is_ldap = is_ldap
User.group_list = group_list
User.archive_list = archive_list


# Customize user admin to include archivist information
class ArchivistUserAdmin(UserAdmin):
    inlines = (ArchivistInline, )
    list_filter = ('archivist__archives', 'is_staff', 'is_superuser',
                   'is_active', 'groups')
    list_display = ('username', 'first_name', 'last_name',
        'is_ldap', 'group_list', 'archive_list', 'is_superuser')

    def get_urls(self):
        return [
            url(r'ldap-user/$', views.init_ldap_user, name='init-ldap-user')
        ] + super(ArchivistUserAdmin, self).get_urls()


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, ArchivistUserAdmin)