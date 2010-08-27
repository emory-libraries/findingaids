from django import forms
from django.db import models
from django.contrib import admin
from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _

from findingaids.simplepages.models import SimplePage

media = settings.MEDIA_URL

class SimplePageForm(forms.ModelForm):
    url = forms.RegexField(label=_("URL"), max_length=100, regex=r'^[-\w/]+$',
        help_text = _("Example: '/about/contact/'. Make sure to have leading"
                      " and trailing slashes."),
        error_message = _("This value must contain only letters, numbers,"
                          " underscores, dashes or slashes."))

    class Meta:
        model = FlatPage


class SimplePageAdmin(admin.ModelAdmin):
    form = SimplePageForm
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content', 'sites')}),
        (_('Advanced options'), {'classes': ('collapse',), 'fields': ('enable_comments', 'registration_required', 'template_name')}),
    )
    list_display = ('url', 'title')
    list_filter = ('sites', 'enable_comments', 'registration_required')
    search_fields = ('url', 'title')

    # Adds the class needed to render TinyMCE
    formfield_overrides = { models.TextField: {'widget': forms.Textarea(attrs={'class':'tinymce'})}, }

    class Media:
        js = (
              #''.join([media, '/js/tinymce/jquery.min.js']),
              'http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js',
              ''.join([media, 'js/tinymce/jscripts/tiny_mce/jquery.tinymce.js']),
             )

admin.site.unregister(FlatPage)
admin.site.register(SimplePage, SimplePageAdmin)