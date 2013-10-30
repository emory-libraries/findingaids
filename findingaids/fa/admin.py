from django.contrib import admin
from django import forms
from findingaids.fa.models import Deleted, Archive

class DeletedAdmin(admin.ModelAdmin):
    list_display = ('eadid', 'title', 'date', 'note')
    list_filter = ('date',)

    # don't allow creating deleted records via admin site
    def has_add_permission(self, request):
        return False

admin.site.register(Deleted, DeletedAdmin)


class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('label', 'name', 'svn')
    prepopulated_fields = {'slug': ('label',)}
    # TODO: if possible, we should make the slug field read only


admin.site.register(Archive, ArchiveAdmin)