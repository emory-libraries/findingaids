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
    