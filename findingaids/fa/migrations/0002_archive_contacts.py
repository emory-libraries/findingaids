# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-13 11:40
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fa', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='archive',
            name='contacts',
            field=models.ManyToManyField(help_text=b'contact person for an archive person to be displayed on the request materials page', to=settings.AUTH_USER_MODEL),
        ),
    ]
