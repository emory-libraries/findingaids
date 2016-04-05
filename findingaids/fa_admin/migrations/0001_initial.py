# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fa', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Archivist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.CommaSeparatedIntegerField(max_length=255, null=True, blank=True)),
                ('archives', models.ManyToManyField(to='fa.Archive', null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Findingaids',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'permissions': (('can_publish', 'Can publish a finding aid'), ('can_preview', 'Can preview a finding aid'), ('can_delete', 'Can delete a finding aid'), ('can_prepare', 'Can prepare a finding aid'), ('can_view_internal_dao', 'Can view internal digital archival objects')),
            },
            bases=(models.Model,),
        ),
    ]
