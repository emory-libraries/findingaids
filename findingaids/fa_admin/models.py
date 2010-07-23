from datetime import datetime
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun

from django.contrib import admin
from django.db import models


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

