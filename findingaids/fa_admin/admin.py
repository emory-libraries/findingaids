from django.contrib import admin
from django.contrib.auth import get_user_model
# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.models import User
from eullocal.django.emory_ldap.admin import EmoryLDAPUserAdmin

from findingaids.fa_admin.models import Archivist

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class ArchivistInline(admin.StackedInline):
    model = Archivist
    can_delete = False
    verbose_name_plural = 'archivist'
    fields = ('archives', )

# Define a new User admin
class UserAdmin(EmoryLDAPUserAdmin):
    inlines = (ArchivistInline, )
    list_filter = ('archivist__archives', 'is_staff', 'is_superuser',
                   'is_active', 'groups')


# Re-register UserAdmin
admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)