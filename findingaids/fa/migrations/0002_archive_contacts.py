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
            field=models.ManyToManyField(blank=True, help_text=b'Contact person for display on the Request Materials page (email required)', to=settings.AUTH_USER_MODEL),
        ),
    ]
