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


def group_list(self):
    return ', '.join(group.name for group in self.groups.all())
group_list.short_description = 'Groups'


def archive_list(self):
    return ', '.join(archive.label for archive in self.archivist.archives.all())
archive_list.short_description = 'Archives'


def is_admin(self):
    return self.is_superuser
is_admin.short_description = 'Admin'
is_admin.boolean = True


def staff_status(self):
    return self.is_staff
staff_status.short_description = 'Staff'
staff_status.boolean = True


User.group_list = group_list
User.archive_list = archive_list
User.is_admin = is_admin
User.staff_status = staff_status


# Customize user admin to include archivist information
class ArchivistUserAdmin(UserAdmin):
    inlines = (ArchivistInline, )
    list_filter = ('archivist__archives', 'is_staff', 'is_superuser',
                   'is_active', 'groups')
    list_display = ('username', 'first_name', 'last_name', 'group_list',
                    'archive_list', 'is_active', 'staff_status',
                    'is_admin')

    def get_urls(self):
        return [
            url(r'ldap-user/$', views.init_ldap_user, name='init-ldap-user')
        ] + super(ArchivistUserAdmin, self).get_urls()


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, ArchivistUserAdmin)