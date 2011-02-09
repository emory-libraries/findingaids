from datetime import datetime

from django.db import models

from findingaids.fa.utils import get_findingaid


class Findingaids(models.Model):
    """
    This model is used as a place holder for custom permissions needed with the
    admin portion of the site.
    """
    class Meta:
        permissions =(
                ("can_publish", "Can publish a finding aid"),
                ("can_preview", "Can preview a finding aid"),
                ("can_delete", "Can delete a finding aid"),
        )

class EadFile:
    """Information about an EAD file available to be published or previewed."""
    def __init__(self, filename, modified):
        self.filename = filename
        self.mtime = modified
        self.modified = datetime.utcfromtimestamp(modified)
        self._published = None
        self._previewed = None
        
    @property
    def published(self):
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
    
    @property
    def previewed(self):
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
            if self._published is None:
                self._previewed = False
        return self._previewed
