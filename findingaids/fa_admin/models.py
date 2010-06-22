from datetime import datetime
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun
from django.db import models

class Permissions(models.Model):
    pass
    class Meta:
        permissions =(
                ("can_publish", "Can publish a finding aid"),
                ("can_preview", "Can preview a finding aid"),
        )

class EAD_Deletion(models.Model):
    filename = models.CharField(max_length = 50)
    title = models.CharField(max_length = 200)
    datetime = models.DateTimeField('date and time deleted')
    reason = models.CharField(max_length = 400)

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

