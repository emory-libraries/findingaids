from django.db import models

class Permissions(models.Model):
    pass
    class Meta:
        permissions =(
                ("can_publish", "Can publish a finding aid"),
                ("can_preview", "Can preview a finding aid"),
        )