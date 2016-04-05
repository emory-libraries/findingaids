# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.management import call_command


DEFAULT_GROUPS = ["Editors", "Publishers"]

def load_fixture(apps, schema_editor):
    'Load default groups.'
    # load initial groups if they are not already present
    Group = apps.get_model("auth", "Group")
    if Group.objects.filter(name__in=DEFAULT_GROUPS).count() == 0:
        call_command('loaddata', 'initial_groups', app_label='fa_admin')

def unload_fixture(apps, schema_editor):
    'Remove default groups.'
    Group = apps.get_model("auth", "Group")

    for group in Group.objects.all():
        if group.name in DEFAULT_GROUPS:
            group.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('fa_admin', '0003_emoryldap_user_to_auth_user'),
        ('auth', '0001_initial'),
        ('contenttypes', '__first__'),
        # requires permissions references for other models:
        ('fa', '0001_initial'),
    ]

    operations = [
            migrations.RunPython(load_fixture,
                reverse_code=unload_fixture, atomic=False)
    ]
