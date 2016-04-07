# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.db import models, migrations, transaction
from django.db.utils  import IntegrityError
from django.conf import settings

# fields common to emory ldap user and auth user
common_fields = ['username', 'password', 'first_name', 'last_name',
   'email', 'is_staff', 'is_active', 'is_superuser']

def copy_user_to_user(a, b):
    # copy common fields, groups, and permissions from user a to user b
    for field in common_fields:
        # only set a field if it is empty
        # - should always be the case for users created by the migration,
        # and will avoid overwriting content for existing users
        if not getattr(b, field):
            setattr(b, field, getattr(a, field))
    b.groups.add(*a.groups.all())
    b.user_permissions.add(*a.user_permissions.all())

    # explicitly copy last login & date joined, no matter
    # what is set on the target user object
    b.last_login = a.last_login
    b.date_joined = a.date_joined

    # NOTE: archivist is related to user, but not handled here


def migrate_ldap_users(apps, schema_editor):
    # get ldap user and standard auth user models
    ldap_user = apps.get_model('emory_ldap', 'EmoryLDAPUser')
    auth_user = apps.get_model('auth', 'user')
    Archivist = apps.get_model('fa_admin', 'archivist')

    id_map = {}
    # create dictionary of archivists by username here?

    # for each ldap user, make sure there is an equivalent auth user
    for ldapuser in ldap_user.objects.all():
        user, created = auth_user.objects.get_or_create(username=ldapuser.username)
        copy_user_to_user(ldapuser, user)
        user.save()
        # keep track ldap user id and corresponding auth user id
        id_map[ldapuser.id] = user.id
        ldapuser.delete()

    # update all archivist ids
    with transaction.atomic():
        for archivist in Archivist.objects.all():
            archivist.user_id = id_map[archivist.user_id]
            archivist.save()



class Migration(migrations.Migration):

    dependencies = [
        ('fa_admin', '0002_user'),
        ('auth', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('emory_ldap', '0002_add_lastlogin_datejoined')
    ]

    operations = [
        migrations.RunPython(migrate_ldap_users, atomic=False),
    ]