# file findingaids/fa_admin/models.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from findingaids.fa.models import Archive
from findingaids.fa.utils import get_findingaid


class Findingaids(models.Model):
    """
    This model is used as a place holder for custom permissions needed with the
    admin portion of the site.
    """
    class Meta:
        permissions = (
                ("can_publish", "Can publish a finding aid"),
                ("can_preview", "Can preview a finding aid"),
                ("can_delete", "Can delete a finding aid"),
                ("can_prepare", "Can prepare a finding aid"),
                ("can_view_internal_dao", "Can view internal digital archival objects"),
        )

class Archivist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    archives = models.ManyToManyField(Archive, blank=True, null=True)
    order = models.CommaSeparatedIntegerField(max_length=255, blank=True,
        null=True)

    def __repr__(self):
        return '<Archivist %s: %s>' % (self.user.username,
            ', '.join(arch.label for arch in self.archives.all()))

    def __unicode__(self):
        return u'Archivist %s (%s)' % (unicode(self.user),
            ', '.join(arch.label for arch in self.archives.all()))

    def sorted_archives(self):
        '''List of archives this user is associated with, in order if
        they have specified any order preference.'''
        archives = self.archives.all()
        # if no archives are explicitly defined and this is a superuser,
        # give them access to all
        if not archives and self.user.is_superuser:
            archives = Archive.objects.all()
        if self.order:
            id_order = [int(id) for id in self.order.split(',')]
            # if id is not present (e.g., new archive), sort to the end
            return sorted(archives,
                key=lambda a: id_order.index(a.id) if a.id in id_order else 50)

        return archives

class EadFile(object):
    """Information about an EAD file available to be published or previewed."""
    def __init__(self, filename, modified, archive=None):
        self.filename = filename
        self.mtime = modified
        self.modified = datetime.utcfromtimestamp(modified)
        self._published = None
        self._previewed = None
        self.archive = archive

    def __repr__(self):
        return '<%s %s>' % (self.__class__, self.filename)

    def get_published(self):
        "Date object was modified in eXist, if published"
        # TODO: previewed & published logic substantially the same; consolidate
        if self._published is None:
            try:
                fa = get_findingaid(filter={'document_name': self.filename},
                                       only=['last_modified'])
                if fa.count():
                    self._published = fa[0].last_modified
            except Exception:
                # FIXME: distinguish between not found and eXist error?
                pass

            # not found or error - store so we don't look it up again
            if self._published is None:
                self._published = False
        return self._published

    def set_published(self, value):
        if value is None:
            self._published = False  # store to prevent xquery lookup
        else:
            self._published = value

    published = property(get_published, set_published)

    def get_previewed(self):
        """Date object was loaded to eXist preview collection, if currently
            available in preview."""
        if self._previewed is None:
            try:
                fa = get_findingaid(filter={'document_name': self.filename},
                                       only=['last_modified'], preview=True)
                if fa.count():
                    self._previewed = fa[0].last_modified
            except Exception:
                pass

            # not found or error - store so we don't look up again
            if self._previewed is None:
                self._previewed = False
        return self._previewed

    def set_previewed(self, value):
        if value is None:
            self._previewed = False  # store to prevent xquery lookup
        else:
            self._previewed = value

    previewed = property(get_previewed, set_previewed)
