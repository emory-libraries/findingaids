# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.management import call_command
from django.contrib.auth.management import create_permissions


DEFAULT_GROUPS = ["Editors", "Publishers"]


def load_fixture(apps, schema_editor):
    'Load default groups.'
    # load initial groups if they are not already present

    # ensure permissions are flushed before loading groups that require them
    # per http://stackoverflow.com/questions/29296757/django-data-migrate-permissions
    apps.models_module = True
    create_permissions(apps, verbosity=0)
    apps.models_module = None

    Group = apps.get_model("auth", "Group")
    if Group.objects.filter(name__in=DEFAULT_GROUPS).count() != len(DEFAULT_GROUPS):
        call_command('loaddata', 'initial_groups', app_label='fa_admin')


def unload_fixture(apps, schema_editor):
    'Remove default groups.'
    Group = apps.get_model("auth", "Group")

    for group in Group.objects.all():
        if group.name in DEFAULT_GROUPS:
            group.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fa_admin', '0001_initial'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
        # requires permissions references for other models:
        ('fa', '0001_initial'),
    ]

    operations = [
            migrations.RunPython(load_fixture,
                reverse_code=unload_fixture, atomic=False)
    ]
