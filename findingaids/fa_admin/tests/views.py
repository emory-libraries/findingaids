# file findingaids/fa_admin/tests/views.py
#
#   Copyright 2012 Emory University Library
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

from mock import patch
import os
import tempfile
from shutil import rmtree
import time

from django.test import Client
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from eulexistdb.db import ExistDB
from eullocal.django.emory_ldap.models import EmoryLDAPUser
from eullocal.django.taskresult.models import TaskResult
from eulexistdb.testutil import TestCase

from findingaids.fa.models import Deleted, Archive
from findingaids.fa_admin import tasks, views
from findingaids.fa_admin.models import EadFile
from findingaids.fa_admin.mocks import MockDjangoPidmanClient  # MockHttplib unused?

### unit tests for findingaids.fa_admin.views

# note: tests for publish view are in a separate test case because
# publish makes use of a celery task, which requires additional setup for testing


class BaseAdminViewsTest(TestCase):
    "Base TestCase for admin views tests.  Common setup/teardown for admin view tests."
    fixtures = ['user']
    credentials = {'superuser': {'username': 'testadmin', 'password': 'secret'},
                   'admin': {'username': 'marbl', 'password': 'marbl'},
                   'no_perms': {'username': 'peon', 'password': 'peon'},
    }
    exist_fixtures = {'files': [
            os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558.xml'),
    ]}

    db = ExistDB()

    def setUp(self):
        self.client = Client()

        # create temporary directory with files for testing
        # - turning off auto-delete so directory and files can be easily cleaned up
        self.tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')
        self.tmpfiles = []
        for num in ['first', 'second', 'third']:
            self.tmpfiles.append(tempfile.NamedTemporaryFile(suffix='.xml',
                    prefix=num + '_', dir=self.tmpdir, delete=False))
            time.sleep(1)        # ensure modification times are different
        # add a non-xml file
        self.nonxml_tmpfile = tempfile.NamedTemporaryFile(suffix='.txt',
                    prefix='nonxml', dir=self.tmpdir, delete=False)

        # temporarily override setting for testing
        if hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
            self._stored_ead_src = settings.FINDINGAID_EAD_SOURCE
        settings.FINDINGAID_EAD_SOURCE = self.tmpdir

        # save the exist collection configs for restoring
        # (some tests changes to simulate an eXist save error)
        self.real_collection = settings.EXISTDB_ROOT_COLLECTION
        self.preview_collection = settings.EXISTDB_PREVIEW_COLLECTION
        self.real_exist_url = settings.EXISTDB_SERVER_URL
        self._existdb_user = getattr(settings, 'EXISTDB_SERVER_USER', None)
        self._existdb_password = getattr(settings, 'EXISTDB_SERVER_PASSWORD', None)

        # save pid config settings to restore in teardown
        self._pid_config = {
            'PIDMAN_HOST': settings.PIDMAN_HOST,
            'PIDMAN_USER': settings.PIDMAN_USER,
            'PIDMAN_PASSWORD': settings.PIDMAN_PASSWORD,
            'PIDMAN_DOMAIN': settings.PIDMAN_DOMAIN
            }
        self._django_pid_client = views.utils.DjangoPidmanRestClient
        views.utils.DjangoPidmanRestClient = MockDjangoPidmanClient

    def tearDown(self):
        if hasattr(self, '_stored_ead_src'):
            settings.FINDINGAID_EAD_SOURCE = self._stored_ead_src

        # clean up temp files & dir
        rmtree(self.tmpdir)

        # restore existdb settings
        settings.EXISTDB_ROOT_COLLECTION = self.real_collection
        settings.EXISTDB_PREVIEW_COLLECTION = self.preview_collection
        settings.EXISTDB_SERVER_URL = self.real_exist_url
        settings.EXISTDB_SERVER_USER = self._existdb_user
        settings.EXISTDB_SERVER_PASSWORD = self._existdb_password

        # restore pid config settings
        for key, val in self._pid_config.iteritems():
            setattr(settings, key, val)

        MockDjangoPidmanClient.search_result = MockDjangoPidmanClient.search_result_nomatches
        views.utils.DjangoPidmanRestClient = self._django_pid_client


class AdminViewsTest(BaseAdminViewsTest):

    def setUp(self):
        # avoid testing difficulties with cached prep-eadxml view
        cache.clear()
        super(AdminViewsTest, self).setUp()

    def test_index(self):
        admin_index = reverse('fa-admin:index')

        # user who can't do anything
        self.client.login(**self.credentials['no_perms'])
        response = self.client.get(admin_index)
        self.assertContains(response, "You don't have permission to do anything",
            msg_prefix='response for user with no permissions includes appropriate message')
        self.assertContains(response, reverse('fa-admin:list-published'), 0,
            msg_prefix='response for user with no permissions does not include link to published docs')
        self.assertContains(response, reverse('fa-admin:preview-ead'), 0,
            msg_prefix='response for user with no permissions does not include link to preview docs')
        self.assertContains(response, 'href="%s"' % reverse('fa-admin:list-staff'), 0,
            msg_prefix='response for user with no permissions does not include link to list/edit staff')
        self.assertContains(response, reverse('admin:index'), 0,
            msg_prefix='response for user with no permissions does not include link to django db admin')

        # user with limited permissions - in findingaid group
        self.client.login(**self.credentials['admin'])
        response = self.client.get(admin_index)
        self.assertContains(response, reverse('fa-admin:list-published'),
            msg_prefix='response for FA admin includes link to published docs')
        self.assertContains(response, reverse('fa-admin:preview-ead'),
            msg_prefix='response for FA admin includes link to preview docs')
        self.assertContains(response, 'href="%s"' % reverse('fa-admin:list-staff'), 0,
            msg_prefix='response for (non super) FA admin does not include link to list/edit staff')
        self.assertContains(response, reverse('admin:index'), 0,
            msg_prefix='response for (non super) FA admin does not include link to django db admin')

        # superuser
        self.client.login(**self.credentials['superuser'])
        response = self.client.get(admin_index)
        self.assertContains(response, 'href="%s"' % reverse('fa-admin:list-staff'),
            msg_prefix='response for superuser includes link to list/edit staff')
        self.assertContains(response, reverse('admin:index'),
            msg_prefix='response for superuser includes link to django db admin')

    def test_recent_files(self):
        admin_index = reverse('fa-admin:index')
        # note: recent files list is currently displayed on main admin page

        # not logged in
        response = self.client.get(admin_index)
        code = response.status_code
        expected = 302
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as AnonymousUser'
                             % (expected, code, admin_index))

        # follow redirects
        response = self.client.get(admin_index, follow=True)
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_("?next=%s" % admin_index in redirect_url)

        # log in as an admin user
        self.client.login(**self.credentials['admin'])
        response = self.client.get(admin_index)
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as admin'
                             % (expected, code, admin_index))

        # file list now loaded in tabs via ajax

    @patch('findingaids.fa_admin.views.files_to_publish')
    def test_list_files(self, mockfilestopub):
        # list of files is specific to an archive, so create a test one
        arch = Archive(label='Manuscripts & Archives', slug='marbl',
            svn='http://svn.example.com/ead/trunk')
        arch.save()

        list_files = reverse('fa-admin:files', kwargs={'archive_id': arch.slug})

        # not logged in
        response = self.client.get(list_files)
        code = response.status_code
        expected = 302
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as AnonymousUser'
                             % (expected, code, list_files))

        # log in as an admin user
        self.client.login(**self.credentials['admin'])

        # nonexistent archive should 404
        bogus_list_files = reverse('fa-admin:files', kwargs={'archive_id': 'nonarchive'})
        response = self.client.get(bogus_list_files)
        self.assertEqual(response.status_code, 404)

        # test actual results
        now = time.time()
        mockfiles = [
            EadFile(filename='ead1.xml', modified=now, archive=arch),
            EadFile(filename='ead2.xml', modified=now, archive=arch),
            EadFile(filename='ead3.xml', modified=now, archive=arch),
        ]
        mockfilestopub.return_value = mockfiles
        response = self.client.get(list_files)
        self.assertEqual(response.status_code, 200)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as admin'
                             % (expected, code, list_files))
        self.assertEqual(len(mockfiles), len(response.context['files'].object_list))
        self.assert_(response.context['show_pages'], "file list view includes list of pages to show")
        # file list contains buttons to preview documents
        preview_url = reverse('fa-admin:preview-ead')
        self.assertContains(response, '<form action="%s" method="post"' % preview_url)

        for f in mockfiles:
            # filename is listed
            self.assertContains(response, f.filename)
            # preview button is present
            self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % f.filename, 1)
            # file list contains link to prep documents
            prep_url = reverse('fa-admin:prep-ead-about',
                args=[os.path.basename(f.filename)])
            self.assertContains(response, 'href="%s?archive=%s">PREP</a>' %
                (prep_url, f.archive.slug))

        # contains pagination
        self.assertPattern('Pages:\s*1', response.content)

        # TODO: test last published date / preview load date?
        # This will require eXist fixtures that match the temp files

        # # simulate configuration error
        # settings.FINDINGAID_EAD_SOURCE = "/does/not/exist"
        # response = self.client.get(list_files)
        # self.assert_("check config file" in response.context['error'])
        # self.assertEqual(0, len(response.context['files'].object_list))

    def test_archive_order(self):
        arch = Archive(label='Manuscripts & Archives', slug='marbl',
            svn='http://svn.example.com/ead/trunk')
        arch.save()

        order_url = reverse('fa-admin:archive-order')

        # log in as an admin user
        self.client.login(**self.credentials['admin'])
        response = self.client.get(order_url)
        code = response.status_code
        expected = 405
        self.assertEqual(code, expected,
            'Expected %s (method not allowed) but returned %s for GET on %s'
            % (expected, code, order_url))

        # post with no data
        response = self.client.post(order_url)
        code = response.status_code
        expected = 400
        self.assertEqual(code, expected,
            'Expected %s (bad request) but returned %s for POST on %s with no data'
            % (expected, code, order_url))

        # create some test archives to test ordering
        marbl = Archive(label='MARBL', name='Manuscipts', svn='https://svn.co/ead',
            slug='marbl')
        marbl.save()
        eua = Archive(label='EUA', name='Archives', svn='https://svn.co/ead',
            slug='eua')
        eua.save()
        theo = Archive(label='Theology', name='Papers', svn='https://svn.co/ead',
            slug='theo')
        theo.save()

        response = self.client.post(order_url, {'ids': '%s,%s' % (eua.slug, theo.slug)})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected,
            'Expected %s but returned %s for POST on %s with valid data'
            % (expected, code, order_url))

        user = EmoryLDAPUser.objects.get(username=self.credentials['admin']['username'])
        # check that order was stored as expected
        self.assertEqual('%d,%d' % (eua.id, theo.id), user.archivist.order)




    def test_preview(self):
        preview_url = reverse('fa-admin:preview-ead')
        self.client.login(**self.credentials['admin'])

        # use fixture directory to test preview
        filename = 'hartsfield558.xml'
        eadid = 'hartsfield558'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        response = self.client.post(preview_url, {'filename': filename},
                follow=True)  # follow redirect so we can inspect message on response
        (redirect_url, code) = response.redirect_chain[0]
        preview_docurl = reverse('fa-admin:preview:findingaid', kwargs={'id': eadid})
        self.assert_(preview_docurl in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
                             % (expected, code, preview_url))
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_("Successfully loaded" in msgs[0],
                "success message present in response context")

        # confirm that document was actually saved to exist
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)
        self.assertEqual(docinfo['name'], settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)

        # GET should just list files available for preview
        response = self.client.get(preview_url)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (GET) as admin user'
                             % (expected, code, preview_url))
        self.assertContains(response, "Hartsfield, William Berry",
            msg_prefix="preview summary should list title of document loaded for preview")
        self.assertContains(response, reverse('fa-admin:preview:findingaid', kwargs={'id': 'hartsfield558'}),
            msg_prefix="preview summary should link to preview page for document loaded to preview")
        self.assertContains(response, 'last modified: 0 minutes ago',
            msg_prefix="preview summary listing includes modification time")

        # preview page should include publish form for users with permission to publish
        preview_fa_url = reverse('fa-admin:preview:findingaid', kwargs={'id': eadid})
        response = self.client.get(preview_fa_url)
        self.assertContains(response,
                '<form id="preview-publish" action="%s" method="post"' % reverse('fa-admin:publish-ead'),
                msg_prefix="preview page includes publish form")
        publish_submit = 'type="submit" name="preview_id" value="%s">PUBLISH' % eadid
        self.assertContains(response, publish_submit,
                msg_prefix="publish form submit button has document eadid for value")

        # clean up
        self.db.removeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)

        # preview invalid document - should display errors
        response = self.client.post(preview_url, {'filename': 'hartsfield558_invalid.xml'})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, invalid document) as admin user'
                             % (expected, code, preview_url))
        self.assertContains(response, "Could not preview")
        self.assertContains(response, """The attribute &#39;invalid&#39; is not allowed""")   # schema validation error
        self.assertContains(response, "Additional Instructions",
                msg_prefix="error page displays instructions & next steps to user")

        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/hartsfield558_invalid.xml')
        self.assertEqual({}, docinfo, "invalid xml document not loaded to exist preview")

        # exist save errors should be caught & handled gracefully
        # - force an error by setting preview collection to a non-existent collection
        settings.EXISTDB_PREVIEW_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(preview_url, {'filename': 'hartsfield558.xml'})
        self.assertContains(response, "Could not preview")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_PREVIEW_COLLECTION)
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

        # simulate incorrect eXist permissions by not specifying username/password
        settings.EXISTDB_PREVIEW_COLLECTION = self.preview_collection   # restore setting
        # ensure guest account cannot update
        self.db.setPermissions(settings.EXISTDB_PREVIEW_COLLECTION, 'other=-update')

        settings.EXISTDB_SERVER_USER = None
        settings.EXISTDB_SERVER_PASSWORD = None

        response = self.client.post(preview_url, {'filename': 'hartsfield558.xml'})
        self.assertContains(response, "Could not preview")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
        self.assertContains(response, "not allowed to write to collection",
                msg_prefix="error page displays specific eXist permission message")

        # - simulate eXist not running by setting existdb url to non-existent exist
        settings.EXISTDB_SERVER_URL = 'http://localhost:9191/not-exist'
        with patch.object(settings, 'EXISTDB_TIMEOUT', new=150):
            response = self.client.post(preview_url, {'filename': 'hartsfield558.xml'})
            self.assertContains(response, "Could not preview")
            self.assertContains(response, "Database Error",
                    msg_prefix="error page displays explanation and instructions to user")
            self.assertContains(response, "I/O Error: Connection refused",
                    msg_prefix="error page displays specific connection error message")

    def test_logout(self):
        admin_logout = reverse('fa-admin:logout')
        # log in as admin user to test logging out
        self.client.login(**self.credentials['admin'])
        response = self.client.get(admin_logout, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('You are now logged out' in msgs[0])

    def test_list_staff(self):
        list_staff = reverse('fa-admin:list-staff')
        # test as an admin with permissions to edit accounts
        self.client.login(**self.credentials['superuser'])
        response = self.client.get(list_staff)
        self.assertContains(response, "Current users")
        # should list users from fixture
        self.assertContains(response, "marbl")
        self.assertContains(response, "peon")

    def test_prep_ead(self):
         # use fixture directory to test publication
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        prep_xml = reverse('fa-admin:prep-ead', args=[filename])
        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        prep_diff = reverse('fa-admin:prep-ead-diff', args=[filename])

        self.client.login(**self.credentials['admin'])
        response = self.client.get(prep_summary)

        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_summary))
        self.assert_(response.context['changes'])

        self.assertContains(response, 'Prepared EAD for %s' % filename)
        self.assertContains(response, 'View file differences line by line')
        self.assertContains(response, prep_diff,
                            msg_prefix="Prepared EAD summary should link to line-by-line diff")
        self.assertPattern('<p class="removed".*>-.*c01.*id=.*s1', response.content)
        self.assertPattern('<p class="added".*>+.*c01.*id=.*hartsfield558_series1.*', response.content)
        self.assertContains(response, prep_xml,
                            msg_prefix="prepared EAD summary should link to xml download")

        response = self.client.get(prep_diff)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_diff))
        # output is generated by difflib; just testing that response has content
        self.assertContains(response, '<table')

        response = self.client.get(prep_xml)
        expected = 200
        self.assertEqual(response.status_code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, response.status_code, prep_xml))
        expected = 'application/xml'
        self.assertEqual(response['Content-Type'], expected, "Expected '%s' but returned '%s' for %s mimetype" % \
                        (expected, response['Content-Type'], prep_xml))
        self.assertEqual(response['Content-Disposition'], "attachment; filename=%s" % filename)
        self.assertContains(response, "xsi:schemaLocation",
                    msg_prefix="response does not lose XSD schema location from original xml")
        self.assertContains(response, "encoding='UTF-8'",
                    msg_prefix="response includes charater encoding declaration")
        self.assertContains(response, "encoding='UTF-8'",
                    msg_prefix="response includes charater encoding declaration")
        self.assertContains(response, 'hartsfield558</eadid>')
        self.assertContains(response, '<c01 level="series" id="hartsfield558_series1"')
        self.assertContains(response, '<c02 level="subseries" id="hartsfield558_subseries6.1"')
        self.assertContains(response, '<index id="hartsfield558_index1">')

        # prep an ead that doesn't need any changes
        filename = 'abbey244.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa',
            'tests', 'fixtures')

        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        response = self.client.get(prep_summary, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (following redirects, prep EAD)'
                             % (expected, code, prep_summary))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (prepared EAD)'
                             % (expected, code, prep_summary))
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_("No changes made to <b>%s</b>" % filename in msgs[0])
        self.assert_("already prepared" in msgs[0])

        # prep an ead that needs an ARK, force ark generation error
        MockDjangoPidmanClient.raise_error = (401, 'unauthorized')
        filename = 'bailey807.xml'
        prep_xml = reverse('fa-admin:prep-ead', args=[filename])
        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        response = self.client.get(prep_summary, follow=True)
        # summary should be 200, display prep error
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected,
            'Expected %s but returned %s for %s (following redirects, prep EAD)' \
             % (expected, code, prep_summary))
        self.assertContains(response, 'Failed to prep the document')
        self.assertContains(response, 'There was an error preparing the file')

        MockDjangoPidmanClient.raise_error = (401, 'unauthorized')
        response = self.client.get(prep_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for %s (prep ead, ARK generation error)' % \
            (expected, response.status_code, prep_xml))

    @patch('findingaids.fa_admin.utils.DjangoPidmanRestClient')
    def test_prep_ark_messages(self, mockpidclient):
        # test that ARK generation messages are displayed to user
        mockpidclient.return_value.search_pids.return_value = {
            'results_count': 2,
            'results': [
                {
                    'pid': '123',
                    'targets': [{'access_uri': 'http://so.me/ark:/123/45b'}, ]
                },
            ]
        }
        # use django test client to login and setup session
        self.client.login(**self.credentials['admin'])

        # use a fixture that does not have an ARK
        filename = 'bailey807.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa',
            'tests', 'fixtures')
        prep_url = reverse('fa-admin:prep-ead-about', kwargs={'filename': filename})
        #expire_view_cache(reverse('fa-admin:prep-ead', kwargs={'filename': filename}))
        response = self.client.get(prep_url)
        # retrieve messages from the request
        msgs = [unicode(m) for m in response.context['messages']
            if m is not None]
        self.assert_('Found 2 ARKs when searching' in msgs[0],
            'multiple ARK warning is set in messages')
        self.assert_('Using existing ARK' in msgs[1],
            'using existing ARK info is set in messages ')

    def test_prep_badlyformedxml(self):
        # use fixture directory to test publication
        filename = 'badlyformed.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        prep_xml = reverse('fa-admin:prep-ead', args=[filename])
        prep_summary = reverse('fa-admin:prep-ead-about', args=[filename])
        prep_diff = reverse('fa-admin:prep-ead-diff', args=[filename])

        self.client.login(**self.credentials['admin'])
        response = self.client.get(prep_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s (non-well-formed xml)' % \
                        (expected, response.status_code, prep_summary))

        response = self.client.get(prep_summary)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_summary))

        self.assertContains(response, 'Could not load document',
                msg_prefix='error loading document displayed')
        self.assertContains(response, 'not allowed in attributes',
                msg_prefix='xml syntax error displayed')
        self.assertNotContains(response, prep_diff,
                msg_prefix="prep summary for badly formed xml should NOT link to line-by-line diff")
        # prep xml link is included in about link; check not present as entire link
        self.assertNotContains(response, 'href="%s"' % prep_xml,
                msg_prefix="prep summary for badly formed xml should NOT link to xml for download")


    def test_list_published(self):
        # login to test admin-only view
        self.client.login(**self.credentials['admin'])

        list_published_url = reverse('fa-admin:list-published')
        response = self.client.get(list_published_url)
        self.assertContains(response, "Published Finding Aids")

        fa = response.context['findingaids']
        self.assert_(fa, "findingaids is set in response context")
        self.assertEqual(fa.object_list[0].eadid.value, 'hartsfield558',
            "fixture document is included in findingaids object list")
        self.assertPattern('Pages:\s*1', response.content,
            "response contains pagination")

    def test_delete_ead(self):
        # login as admin to test admin-only feature
        self.client.login(**self.credentials['admin'])

        eadid = 'hartsfield558'
        delete_url = reverse('fa-admin:delete-ead', kwargs={'id': eadid})
        # GET - should display delete form with eadid & title from document
        response = self.client.get(delete_url)
        self.assertEqual(eadid, unicode(response.context['form']['eadid'].value()))
        self.assertEqual("William Berry Hartsfield papers, circa 1860s-1983",
                         response.context['form']['title'].value())

        # POST form data to trigger a deletion
        title, note = 'William Berry Hartsfield papers', 'Moved to another archive.'
        response = self.client.post(delete_url, {'eadid': eadid, 'title': title,
                                    'note': note, 'date': '2010-07-01 15:01:20'}, follow=True)
        # on success:
        # - the document should have been removed from eXist
        self.assertFalse(self.db.hasDocument('%s/%s.xml' % (settings.EXISTDB_TEST_COLLECTION, eadid)),
            "document should no longer be present in eXist collection after delete_ead")
        # - a Deleted db record should have been created with posted data
        deleted_info = Deleted.objects.get(eadid=eadid)
        self.assertEqual(eadid, deleted_info.eadid, "deleted record has correct eadid")
        self.assertEqual(title, deleted_info.title, "deleted record has correct ead title")
        self.assertEqual(note, deleted_info.note, "deleted record has posted note")
        # - the user should be redirected with a success message
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(redirect_url.endswith(reverse('fa-admin:list-published')),
            "response redirects to list of published documents")
        expected = 303      # redirect - see other
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST)'
                             % (expected, code, delete_url))
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Successfully removed <b>%s</b>.' % eadid in msgs[0],
                "delete success message is set in response context")

        # test for expected failures for a non-existent eadid
        eadid = 'bogus-id'
        delete_nonexistent = reverse('fa-admin:delete-ead', kwargs={'id': eadid})
        # GET - attempt to load form to delete an ead not present in eXist db
        response = self.client.get(delete_nonexistent, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assertEqual("Error: could not retrieve <b>%s</b> for deletion." \
                % eadid, msgs[0],
                "'not found' message set in response context when attempting to " +
                " GET delete form for a nonexistent eadid")
        # POST - attempt to actually delete an ead that isn't in eXist
        response = self.client.post(delete_nonexistent, {'eadid': eadid, 'title': title,
                                                'note': note}, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assertEqual("Error: could not retrieve <b>%s</b> for deletion." \
                % eadid, msgs[0],
                "'not found' message set in response context when attempting to " +
                "POST delete form for a nonexistent eadid")

        # FIXME: not sure how to trigger or simulate the error case where the
        # finding aid is loaded from eXist but actual deletion fails...

    def test_redelete(self):
        # test deleting when there is already an existing deleted record in the DB
        # (e.g., document was published, deleted, re-published, and now being deleted again)
        # - update existing delete_info with new values to simplify testing

        self.client.login(**self.credentials['admin'])
        eadid = 'hartsfield558'
        delete_url = reverse('fa-admin:delete-ead', kwargs={'id': eadid})

        title, note = 'Deleted EAD record', 'removed because of foo'
        Deleted(eadid=eadid, title=title, note=note).save()

        # GET: form should display info from existing Deleted record
        response = self.client.get(delete_url)
        self.assert_('William Berry Hartsfield papers' in
                     response.context['form']['title'].value(),
                     'edit form contains title from Finding Aid (overrides title from DB)')
        self.assertContains(response, '%s</textarea>' % note,
            msg_prefix="edit form contains notes from previous deletion")
        # POST form data to trigger a deletion and update deleted record
        new_title, new_note = 'William Berry Hartsfield papers', 'Moved to another archive.'
        new_date = '2011-08-09 15:01:20'
        response = self.client.post(delete_url, {'eadid': eadid, 'title': new_title,
                                    'note': new_note, 'date': new_date}, follow=True)
        # *existing* deleted DB record should be updated with posted data
        deleted_info = Deleted.objects.get(eadid=eadid)
        self.assertEqual(new_title, deleted_info.title)
        self.assertEqual(new_note, deleted_info.note)


# unit tests for views that make use of celery tasks (additional setup required)

def _celerytest_setUp(testcase):
    # FIXME: duplicated in fa_admin.tests.utils

    # ensure required settings are available for testing
    if hasattr(settings, 'PROXY_HOST'):
        testcase.proxy_host = settings.PROXY_HOST
        setattr(settings, 'PROXY_HOST', 'myproxy:10101')
    if hasattr(settings, 'SITE_BASE_URL'):
        testcase.site_base_url = settings.SITE_BASE_URL
        setattr(settings, 'SITE_BASE_URL', 'http://findingaids.test.edu')

    # OK, this is a little weird: swap out the real httplib in tasks with
    # the mock httplib object defined above
    # testcase.real_httplib = tasks.httplib
    # testcase.mock_httplib = MockHttplib()
    # tasks.httplib = testcase.mock_httplib


def _celerytest_tearDown(testcase):
        if testcase.proxy_host:
            settings.PROXY_HOST = testcase.proxy_host
        if testcase.site_base_url:
            settings.SITE_BASE_URL = testcase.site_base_url


# in test mode, celery task returns an EagerResult with no task id
# intercept the result from the real task and add a task id for testing
class Mock_reload_pdf:
    def delay(self, eadid):
        result = tasks.reload_cached_pdf.delay(eadid)
        result.task_id = "test-task-id"
        return result


@patch.object(settings, 'CELERY_ALWAYS_EAGER', new=True)
class CeleryAdminViewsTest(BaseAdminViewsTest):

    def setUp(self):
        super(CeleryAdminViewsTest, self).setUp()
        _celerytest_setUp(self)

        # swap out celery task in views with our mock version
        self.real_reload = views.reload_cached_pdf
        views.reload_cached_pdf = Mock_reload_pdf()

    def tearDown(self):
        super(CeleryAdminViewsTest, self).tearDown()
        _celerytest_tearDown(self)

        # restore the real celery task
        views.reload_cached_pdf = self.real_reload

    # use fixture directory to test publication
    @patch.object(settings, 'FINDINGAID_EAD_SOURCE', new=os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures'))
    def test_publish(self):

        # first test only uses temp dir & files created in setup
        with patch.object(settings, 'FINDINGAID_EAD_SOURCE', new=self.tmpdir):
            publish_url = reverse('fa-admin:publish-ead')
            self.client.login(**self.credentials['admin'])
            # GET should just list files available to be published
            response = self.client.get(publish_url)

        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (GET) as admin user'
            % (expected, code, publish_url))

        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        # use fixture directory to test publication
        filename = 'hartsfield558.xml'
        response = self.client.post(publish_url, {'filename': filename}, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, following redirects) as admin user'
            % (expected, code, publish_url))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
            % (expected, code, publish_url))

        # convert messages into an easier format to test
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_("Successfully updated" in msgs[0], "success message set in context")

        # confirm that document was actually saved to exist
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)

        task = TaskResult.objects.get(object_id='hartsfield558')
        self.assert_(isinstance(task, TaskResult),
            "TaskResult was created in db for pdf reload after successful publish")

        # publish invalid document - should display errors
        response = self.client.post(publish_url, {'filename': 'hartsfield558_invalid.xml'})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, invalid document) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "The attribute &#39;invalid&#39; is not allowed")   # DTD validation error
        self.assertContains(response, "series c01 id attribute is not set")
        self.assertContains(response, "index id attribute is not set")
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/hartsfield558_invalid.xml')
        self.assertEqual({}, docinfo)   # invalid document not loaded to exist

        # attempt to publish non-well-formed xml - display errors
        with patch.object(settings, 'FINDINGAID_EAD_SOURCE', new=fixture_dir):
            response = self.client.post(publish_url, {'filename': 'badlyformed.xml'})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, not well-formed xml) as admin user'
                             % (expected, code, publish_url))
        self.assertContains(response, "Could not publish")
        self.assertContains(response, "Unescaped &#39;&lt;&#39; not allowed in attributes values",
            msg_prefix="syntax error detail for badly formed XML displays")

        # exist save errors should be caught & handled gracefully
        # - force an exist save error by setting collection to a non-existent collection
        with patch.object(settings, 'EXISTDB_ROOT_COLLECTION', new='/bogus/doesntexist'):
            response = self.client.post(publish_url, {'filename': 'hartsfield558.xml'})
            self.assertContains(response, "Could not publish",
                msg_prefix="exist save error on publish displays error to user")
            self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_ROOT_COLLECTION,
                msg_prefix="specific exist save error displayed to user")
            self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

        # simulate incorrect eXist permissions by not specifying username/password
                # ensure guest account cannot update
        self.db.setPermissions(settings.EXISTDB_ROOT_COLLECTION, 'other=-update')
        with patch.object(settings, 'EXISTDB_SERVER_USER', new=None):
            with patch.object(settings, 'EXISTDB_SERVER_PASSWORD', new=None):

                response = self.client.post(publish_url, {'filename': 'hartsfield558.xml'})
                self.assertContains(response, "Could not publish")
                self.assertContains(response, "Database Error",
                    msg_prefix="error page displays explanation and instructions to user")
                self.assertContains(response, "update is not allowed",
                    msg_prefix="error page displays specific exist permissions message")

        # - simulate eXist not running by setting existdb url to non-existent exist
        with patch.object(settings, 'EXISTDB_SERVER_URL', new='http://localhost:9191/not-exist'):
            response = self.client.post(publish_url, {'filename': 'hartsfield558.xml'})
            self.assertContains(response, "Could not publish")
            self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")
            self.assertContains(response, "I/O Error: Connection refused",
                msg_prefix="error page displays specific connection error message")

    def test_publish_from_preview(self):
        # test publishing a document that has been loaded for preview
        publish_url = reverse('fa-admin:publish-ead')
        self.client.login(**self.credentials['admin'])

        # load a file to preview to test
        filename = 'hartsfield558.xml'
        settings.FINDINGAID_EAD_SOURCE = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        response = self.client.post(reverse('fa-admin:preview-ead'), {'filename': filename})

        # publish the preview file
        response = self.client.post(publish_url, {'preview_id': 'hartsfield558'}, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST, following redirects) as admin user'
                             % (expected, code, publish_url))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
                             % (expected, code, publish_url))

        # convert mesages into an easier format to test
        msgs = [str(msg) for msg in response.context['messages']]
        # last message is the publication one (preview load message still in message queue)
        self.assert_("Successfully updated" in msgs[-1],
            "publication success message set in response context")
        self.assert_('href="%s"' % reverse('fa:findingaid',
            kwargs={'id': 'hartsfield558'}) in msgs[-1],
            'success message links to published document')
        self.assert_('William Berry Hartsfield papers' in msgs[-1],
            'success message includes unit title of published document')

        # confirm that document was moved to main collection
        docinfo = self.db.describeDocument(settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        self.assertEqual(docinfo['name'], settings.EXISTDB_TEST_COLLECTION + '/' + filename)
        # confirm that document is no longer in preview collection
        docinfo = self.db.describeDocument(settings.EXISTDB_PREVIEW_COLLECTION + '/' + filename)
        self.assertEqual({}, docinfo)

        task = TaskResult.objects.get(object_id='hartsfield558')
        self.assert_(isinstance(task, TaskResult),
            "TaskResult was created in db for pdf reload after successful publish from preview")

        # attempt to publish a document NOT loaded to preview
        response = self.client.post(publish_url, {'preview_id': 'bogus345'}, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Publish failed. Could not retrieve' in msgs[0],
            'error message set in response context attempting to publish a document not in preview')

        # force an exist save error by setting collection to a non-existent collection
        real_collection = settings.EXISTDB_ROOT_COLLECTION
        settings.EXISTDB_ROOT_COLLECTION = "/bogus/doesntexist"
        response = self.client.post(publish_url, {'filename': 'hartsfield558.xml'})
        self.assertContains(response, "Could not publish",
                msg_prefix="exist save error on publish displays error to user")
        self.assertContains(response,
                "Collection %s not found" % settings.EXISTDB_ROOT_COLLECTION,
                msg_prefix="specific exist save error displayed to user")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

        # restore settings
        settings.EXISTDB_ROOT_COLLECTION = real_collection

