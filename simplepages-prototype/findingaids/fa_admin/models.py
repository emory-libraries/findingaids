from datetime import datetime
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun

from django.contrib import admin
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


# store details about pdf reload celery task results for display on admin page
class TaskResult(models.Model):
    label = models.CharField(max_length=100)
    eadid = models.CharField(max_length=50)
    created = models.DateTimeField(default=datetime.now)
    task_id = models.CharField(max_length=100)
    task_start = models.DateTimeField(blank=True, null=True)
    task_end = models.DateTimeField(blank=True, null=True)

    def task(self):
        return AsyncResult(self.task_id)

    def __unicode__(self):
        return self.label

    def duration(self):
        if self.task_end and self.task_start:
            return self.task_end - self.task_start
        else:
            return ''

# listeners to celery signals to store start and end time for tasks
# NOTE: these functions do not filter on the sender/task function

def taskresult_start(sender, task_id, **kwargs):
    try:
        tr = TaskResult.objects.get(task_id=task_id)
        tr.task_start = datetime.now()
        tr.save()
    except Exception:
        pass
task_prerun.connect(taskresult_start)

def taskresult_end(sender, task_id, **kwargs):
    try:
        tr = TaskResult.objects.get(task_id=task_id)
        tr.task_end = datetime.now()
        tr.save()
    except Exception:
        pass
task_postrun.connect(taskresult_end)

class TaskResultAdmin(admin.ModelAdmin):
    list_display = ('eadid', 'label', 'created', 'task_start', 'task_end', 'duration')
    list_filter  = ('created',)
    # disallow creating task results via admin site
    def has_add_permission(self, request):
        return False

admin.site.register(TaskResult, TaskResultAdmin)

