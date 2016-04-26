# file findingaids/fa_admin/tests/models.py
#
#   Copyright 2013 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from django.test import TestCase
from django.contrib.auth import get_user_model

from findingaids.fa.models import Archive
from findingaids.fa_admin.models import Archivist


User = get_user_model()


class ArchivistTestCase(TestCase):
    fixtures = ['user']

    def test_sorted_archives(self):
        # create some test archives to associate with test user
        marbl = Archive(label='MARBL', name='Manuscipts', svn='https://svn.co/ead',
            slug='marbl')
        marbl.save()
        eua = Archive(label='EUA', name='Archives', svn='https://svn.co/ead',
            slug='eua')
        eua.save()
        theo = Archive(label='Theology', name='Papers', svn='https://svn.co/ead',
            slug='theo')
        theo.save()
        # NOTE: consider making this a fixture?

        # no archives or order = empty list, no errors
        arc = Archivist(user=User.objects.get(username='testadmin'))
        arc.save()
        # because admin is super, should see all archives
        self.assertEqual(3, arc.sorted_archives().count())

        arc.archives.add(marbl, eua, theo)
        arc.user.is_superuser = False
        # no order
        default = Archive.objects.all()
        self.assertEqual([a.id for a in default],
            [a.id for a in arc.sorted_archives()])

        # partial order
        arc.order = ','.join([str(eua.id), str(theo.id)])
        ordered_archives = arc.sorted_archives()
        self.assertEqual(eua.id, ordered_archives[0].id)
        self.assertEqual(theo.id, ordered_archives[1].id)
        # since not specified, should be put last
        self.assertEqual(marbl.id, ordered_archives[2].id)

        # no explicit archives and not super = empty list
        arc.archives.clear()
        self.assertEqual([], arc.sorted_archives())
