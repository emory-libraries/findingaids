# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(help_text=b'Short label to identify an archive', max_length=10)),
                ('name', models.CharField(help_text=b'repository name (subarea) in EAD to identify finding aids associated with this archive', max_length=255)),
                ('svn', models.URLField(help_text=b'URL to subversion repository containing EAD for this archive', verbose_name=b'Subversion Repository')),
                ('slug', models.SlugField(help_text=b'shorthand id\n        (auto-generated from label; do not modify after initial archive definition)')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Deleted',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('eadid', models.CharField(unique=True, max_length=50, verbose_name=b'EAD Identifier')),
                ('title', models.CharField(max_length=200)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date removed')),
                ('note', models.CharField(help_text=b'Optional: Enter the reason this document is being deleted. These comments will be displayed to anyone who had the finding aid bookmarked and returns after it is gone.', max_length=400, blank=True)),
            ],
            options={
                'verbose_name': 'Deleted Record',
            },
            bases=(models.Model,),
        ),
    ]
