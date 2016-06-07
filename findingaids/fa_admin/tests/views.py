# file findingaids/fa_admin/tests/views.py
# -*- coding: utf-8 -*-
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

import filecmp
from mock import patch
import os
import tempfile
from shutil import rmtree, copyfile
import time
import unittest

from django.test import Client
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from eulexistdb.db import ExistDB
from eullocal.django.taskresult.models import TaskResult
from eulexistdb.testutil import TestCase
from eulxml.xmlmap import load_xmlobject_from_file

from findingaids.fa.models import Deleted, Archive, FindingAid
from findingaids.fa_admin import tasks, views
from findingaids.fa_admin.models import EadFile
from findingaids.fa_admin.mocks import MockDjangoPidmanClient  # MockHttplib unused?

### unit tests for findingaids.fa_admin.views

# note: tests for publish view are in a separate test case because
# publish makes use of a celery task, which requires additional setup for testing

skipIf_no_proxy = unittest.skipIf('HTTP_PROXY' not in os.environ,
    'Schema validation test requires an HTTP_PROXY')

User = get_user_model()


class BaseAdminViewsTest(TestCase):
    "Base TestCase for admin views tests.  Common setup/teardown for admin view tests."
    fixtures = ['user', 'archivist', 'archives']
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

        # FIXME: use override_settings instead
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
    # test for views that require eXist full-text index
    exist_fixtures = {
        'files': [
            os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures', 'hartsfield558.xml'),
            ],
        'index': settings.EXISTDB_INDEX_CONFIGFILE
        # NOTE: full-text index required for published documents by archive
        # could split out full-text specific tests if it gets too slow
    }

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
        # TODO: resolve preview list view (going away? archive specific)
        # self.assertContains(response, reverse('fa-admin:preview-ead', kwargs={'archive': archive.slug}), 0,
        #     msg_prefix='response for user with no permissions does not include link to preview docs')
        self.assertContains(response, 'href="%s"' % reverse('admin:auth_user_changelist'), 0,
            msg_prefix='response for user with no permissions does not include link to list/edit staff')
        self.assertContains(response, 'href="%s"' % reverse('admin:index'), 0,
            msg_prefix='response for user with no permissions does not include link to django db admin')

        # user with limited permissions - in findingaid group, associated with first archive
        self.client.login(**self.credentials['admin'])
        response = self.client.get(admin_index)
        self.assertNotContains(response, reverse('fa-admin:list-published'),
            msg_prefix='response for non-superuser FA admin does not link to all published docs')

        # archive-specific published lists only
        user = User.objects.get(username=self.credentials['admin']['username'])
        for archive in user.archivist.archives.all():
            self.assertContains(response, reverse('fa-admin:published-by-archive',
                kwargs={'archive': archive.slug}),
               msg_prefix='response for FA admin includes link to published docs for %s' % archive.slug)
        # TODO: resolve preview list view (going away? archive specific)
        # self.assertContains(response, reverse('fa-admin:preview-ead', kwargs={'archive': archive.slug}),
        #     msg_prefix='response for FA admin includes link to preview docs')
        self.assertContains(response, 'href="%s"' % reverse('admin:auth_user_changelist'), 0,
            msg_prefix='response for (non super) FA admin does not include link to list/edit staff')
        self.assertContains(response, 'href="%s"' % reverse('admin:index'), 0,
            msg_prefix='response for (non super) FA admin does not include link to django db admin')

        # superuser
        self.client.login(**self.credentials['superuser'])
        response = self.client.get(admin_index)
        self.assertContains(response, 'href="%s"' % reverse('admin:auth_user_changelist'),
            msg_prefix='response for superuser includes link to list/edit staff')
        self.assertContains(response, reverse('admin:index'),
            msg_prefix='response for superuser includes link to django db admin')
        self.assertContains(response, reverse('fa-admin:list-published'),
            msg_prefix='response for superuser links to list of all published docs')

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
        # using fixture archives
        arch = Archive.objects.get(slug='marbl')
        list_files = reverse('fa-admin:files', kwargs={'archive': arch.slug})

        # not logged in
        response = self.client.get(list_files)
        code = response.status_code
        expected = 302
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s as AnonymousUser'
                             % (expected, code, list_files))

        # log in as an superuser
        self.client.login(**self.credentials['superuser'])

        # nonexistent archive should 404
        bogus_list_files = reverse('fa-admin:files', kwargs={'archive': 'nonarchive'})
        response = self.client.get(bogus_list_files)
        self.assertEqual(response.status_code, 404)
        # NOTE: for non-superuser this returns 302 because user doesn't have
        # permissions on a non-existent archive

        # login as admin user
        self.client.login(**self.credentials['admin'])

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
        preview_url = reverse('fa-admin:preview-ead', kwargs={'archive': arch.slug})
        self.assertContains(response, '<form action="%s" method="post"' % preview_url)

        for f in mockfiles:
            # filename is listed
            self.assertContains(response, f.filename)
            # preview button is present
            self.assertContains(response, '<button type="submit" name="filename" value="%s" '
                % f.filename, 1)
            # file list contains link to prep documents
            prep_url = reverse('fa-admin:prep-ead-about',
                kwargs={
                    'filename': os.path.basename(f.filename),
                    'archive': f.archive.slug
                })
            self.assertContains(response, 'href="%s">PREP</a>' % prep_url)

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

        # load archive fixtures to test ordering
        marbl = Archive.objects.get(slug='marbl')
        eua = Archive.objects.get(slug='eua')
        theo = Archive.objects.get(slug='pitts')

        response = self.client.post(order_url, {'ids': '%s,%s' % (eua.slug, theo.slug)})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected,
            'Expected %s but returned %s for POST on %s with valid data'
            % (expected, code, order_url))

        user = User.objects.get(username=self.credentials['admin']['username'])
        # check that order was stored as expected
        self.assertEqual('%d,%d' % (eua.id, theo.id), user.archivist.order)

    @skipIf_no_proxy
    def test_preview(self):
        arch = Archive.objects.all()[0]
        preview_url = reverse('fa-admin:preview-ead', kwargs={'archive': arch.slug})
        self.client.login(**self.credentials['admin'])

        # use fixture directory to test preview
        filename = 'hartsfield558.xml'
        eadid = 'hartsfield558'
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.post(preview_url, {'filename': filename,
                'archive': arch.slug},
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
        # NOTE: preview list view doesn't currently use archive; this functionality
        # needs to either be removed, separated, or filter on archive
        response = self.client.get(preview_url, {'archive': arch.slug})
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (GET) as admin user'
                             % (expected, code, preview_url))
        self.assertContains(response, "Hartsfield, William Berry",
            msg_prefix="preview summary should list title of document loaded for preview")
        self.assertContains(response, reverse('fa-admin:preview:findingaid', kwargs={'id': 'hartsfield558'}),
            msg_prefix="preview summary should link to preview page for document loaded to preview")
        self.assertContains(response, 'last modified: 0 minutes ago',
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
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
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

        # NOTE: previously using a non-existent preview collection would
        # cause an error, but now eXist creates the collection automatically

        # simulate incorrect eXist permissions by not specifying username/password
        # ensure guest account cannot update
        # self.db.setPermissions(settings.EXISTDB_PREVIEW_COLLECTION, 'other=-write,update')
        # NOTE: string syntax should still be valid according to the docs,
        # but it results in an error where this does not
        self.db.setPermissions(settings.EXISTDB_PREVIEW_COLLECTION, 0774)

        fake_collection = '/bogus/doesntexist'
        with override_settings(EXISTDB_SERVER_USER=None,
                               EXISTDB_SERVER_PASSWORD=None,
                               EXISTDB_PREVIEW_COLLECTION=fake_collection):
            with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
                response = self.client.post(preview_url, {'filename': 'hartsfield558.xml'})

        self.assertContains(response, "Could not preview")
        self.assertContains(response, "Failed to load the document",
                msg_prefix="error page displays explanation and instructions to user")

        # - simulate eXist not running by setting existdb url to non-existent exist
        with override_settings(EXISTDB_SERVER_URL='http://localhost:9191/not-exist',
            EXISTDB_TIMEOUT=150):
            with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
                response = self.client.post(preview_url, {'filename': 'hartsfield558.xml'})

        self.assertContains(response, "Could not preview")
        self.assertContains(response, "Database Error",
                msg_prefix="error page displays explanation and instructions to user")

    def test_logout(self):
        admin_logout = reverse('fa-admin:logout')
        # log in as admin user to test logging out
        self.client.login(**self.credentials['admin'])
        response = self.client.get(admin_logout, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('You are now logged out' in msgs[0])

    def test_prep_ead(self):
        # use fixture directory to test publication
        arch = Archive.objects.all()[0]
        filename = 'hartsfield558.xml'
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        url_args = {'filename': filename, 'archive': arch.slug}
        prep_xml = reverse('fa-admin:prep-ead', kwargs=url_args)
        prep_summary = reverse('fa-admin:prep-ead-about', kwargs=url_args)
        prep_diff = reverse('fa-admin:prep-ead-diff', kwargs=url_args)

        self.client.login(**self.credentials['admin'])
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.get(prep_summary)

        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_summary))
        # FIXME: same type of error loading document before it gets to
        # the logic tested here
        self.assert_(response.context['changes'])

        self.assertContains(response, 'Prepared EAD for %s' % filename)
        self.assertContains(response, 'View file differences line by line')
        self.assertContains(response, prep_diff,
                            msg_prefix="Prepared EAD summary should link to line-by-line diff")
        self.assertPattern('<p class="removed".*>-.*c01.*id=.*s1', response.content)
        self.assertPattern('<p class="added".*>+.*c01.*id=.*hartsfield558_series1.*', response.content)
        self.assertContains(response, prep_xml,
                            msg_prefix="prepared EAD summary should link to xml download")

        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.get(prep_diff)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_diff))
        # output is generated by difflib; just testing that response has content
        self.assertContains(response, '<table')

        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
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
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa', 'tests', 'fixtures')

        prep_summary = reverse('fa-admin:prep-ead-about', kwargs={'filename': filename,
            'archive': arch.slug})
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
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
        url_args = {'filename': filename, 'archive': arch.slug}
        prep_xml = reverse('fa-admin:prep-ead', kwargs=url_args)
        prep_summary = reverse('fa-admin:prep-ead-about', kwargs=url_args)
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
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
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.get(prep_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
            'Expected %s but returned %s for %s (prep ead, ARK generation error)' % \
            (expected, response.status_code, prep_xml))

        # use POST to prep-ead to save changes in subversion
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        filename = 'hartsfield558.xml'
        url_args = {'filename': filename, 'archive': arch.slug}
        prep_xml = reverse('fa-admin:prep-ead', kwargs=url_args)
        # copy into a temp dir since the view will modify the file
        tmpdir = tempfile.mkdtemp('fa-prep')
        copy, fixture = os.path.join(fixture_dir, filename), os.path.join(tmpdir, filename)
        copyfile(copy, fixture)

        with patch('findingaids.fa.models.Archive.svn_local_path', tmpdir):
            with patch('findingaids.fa_admin.views.svn_client') as svn_client:
                # simulate successful commit
                svn_client.return_value.commit.return_value = (8, '2013-11-13T18:19:00.191382Z', 'keep')
                # delete
                cache.delete(filename)
                response = self.client.post(prep_xml, follow=True)

        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Committed changes ' in msgs[0])
        # check that file has been modified
        self.assertFalse(filecmp.cmp(copy, fixture),
            'prepared file should have been modified')

        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(redirect_url.endswith(reverse('fa-admin:index')),
            "response should redirect to main admin page")

       # simulate commit with no changes
        with patch('findingaids.fa.models.Archive.svn_local_path', tmpdir):
            with patch('findingaids.fa_admin.views.svn_client') as svn_client:
                svn_client.return_value.commit.return_value = None
                response = self.client.post(prep_xml, follow=True)

        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('No changes to commit ' in msgs[0])
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(redirect_url.endswith(reverse('fa-admin:index')),
            "response should redirect to main admin page even if no changes are committed")



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
        user = User.objects.get(username=self.credentials['admin']['username'])
        arch = user.archivist.archives.all()[0]

        # use a fixture that does not have an ARK
        filename = 'bailey807.xml'
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa',
            'tests', 'fixtures')
        prep_url = reverse('fa-admin:prep-ead-about',
           kwargs={'filename': filename, 'archive': arch.slug})
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.get(prep_url)

        # retrieve messages from the request
        msgs = [unicode(m) for m in response.context['messages']
            if m is not None]
        # FIXME: this test is failing because there is an error loading the file
        # before it ever gets to the mock pidman error

        self.assert_('Found 2 ARKs when searching' in msgs[0],
            'multiple ARK warning is set in messages')
        self.assert_('Using existing ARK' in msgs[1],
            'using existing ARK info is set in messages ')

    def test_prep_badlyformedxml(self):
        # use fixture directory to test publication
        arch = Archive.objects.all()[0]
        filename = 'badlyformed.xml'
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')

        url_args = {'filename': filename, 'archive': arch.slug}
        prep_xml = reverse('fa-admin:prep-ead', kwargs=url_args)
        prep_summary = reverse('fa-admin:prep-ead-about', kwargs=url_args)
        prep_diff = reverse('fa-admin:prep-ead-diff', kwargs=url_args)

        self.client.login(**self.credentials['admin'])
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.get(prep_xml)
        expected = 500
        self.assertEqual(response.status_code, expected,
                        'Expected %s but returned %s for %s (non-well-formed xml)' % \
                        (expected, response.status_code, prep_summary))
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.get(prep_summary)
        code = response.status_code
        expected = 200
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s' % \
                        (expected, code, prep_summary))
        # FIXME: test is failing because document fails to load before
        # we get to the expected error
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

    def test_published_by_archive(self):
        self.client.login(**self.credentials['admin'])

        archive = Archive.objects.get(slug='marbl')
        arch_published_url = reverse('fa-admin:published-by-archive',
            kwargs={'archive': archive.slug})
        response = self.client.get(arch_published_url)
        self.assertContains(response, "Published Finding Aids for %s" % archive.name)

        fa = response.context['findingaids']

        self.assert_(fa, "findingaids result is set in response context")
        self.assertEqual(fa.object_list[0].eadid.value, 'hartsfield558',
            "fixture document is included in findingaids object list")
        self.assertPattern('Pages:\s*1', response.content,
            "response contains pagination")


    def test_delete_ead(self):
        # login as admin to test admin-only feature
        self.client.login(**self.credentials['admin'])

        eadid = 'hartsfield558'
        # use archive-specific delete form for non-superuser admin
        delete_url = reverse('fa-admin:delete-ead-by-archive',
            kwargs={'id': eadid, 'archive': 'marbl'})
        # GET - should display delete form with eadid & title from document
        response = self.client.get(delete_url)
        self.assertEqual(eadid, unicode(response.context['form']['eadid'].value()))
        self.assertEqual("William Berry Hartsfield papers, circa 1860s-1983",
                         response.context['form']['title'].value())

        # POST form data to trigger a deletion
        title, note = 'William Berry Hartsfield papers', 'Moved to another archive.'

        # temporarily remove access to archive to test permission logic
        user = User.objects.get(username=self.credentials['admin']['username'])
        marbl = Archive.objects.get(slug='marbl')
        user.archivist.archives.remove(marbl)
        user.save()
        response = self.client.post(delete_url, {'eadid': eadid, 'title': title,
                                    'note': note, 'date': '2010-07-01 15:01:20'}, follow=False)
        code = response.status_code
        expected = 302   # permission denied - currently redirects to login form (even if logged in)
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s for user without archive access'
                         % (expected, code, delete_url))
        # - the document should NOT have been removed from eXist
        self.assertTrue(self.db.hasDocument('%s/%s.xml' % (settings.EXISTDB_TEST_COLLECTION, eadid)),
            "document should be present in eXist collection when user has insufficient access for delete_ead")

        # restore access
        user.archivist.archives.add(marbl)
        user.save()
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
        self.assert_(redirect_url.endswith(reverse('fa-admin:published-by-archive',
            kwargs={'archive': 'marbl'})),
            "response redirects to archive-specific list of published documents")
        expected = 303      # redirect - see other
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST)'
                             % (expected, code, delete_url))
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Successfully removed <b>%s</b>.' % eadid in msgs[0],
                "delete success message is set in response context")

        # test for expected failures for a non-existent eadid
        # NOTE: logging in as superuser, because non-super admin will be denied
        # based on lack of archive information
        self.client.login(**self.credentials['superuser'])
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
        delete_url = reverse('fa-admin:delete-ead-by-archive',
            kwargs={'id': eadid, 'archive': 'marbl'})

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

    @skipIf_no_proxy
    def test_publish(self):
        # publish from file no longer supported; publish from preview only
        self.client.login(**self.credentials['admin'])

        publish_url = reverse('fa-admin:publish-ead')
        # post without preview id should error - message + redirect
        response = self.client.post(publish_url, follow=True)
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s without preview id'
            % (expected, code, publish_url))

        # convert messages into an easier format to test
        msgs = [str(msg) for msg in response.context['messages']]
        self.assertEqual('No preview document specified for publication',
            msgs[0], 'message should indicate no preview document specified')

        # use fixture directory to test publication
        fixture_dir = os.path.join(settings.BASE_DIR, 'fa_admin', 'fixtures')
        # load a file to preview for testing
        filename = 'hartsfield558.xml'
        # override archive svn working path to use fixture dir to load preview
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.post(reverse('fa-admin:preview-ead', kwargs={'archive': 'marbl'}),
                {'filename': filename})

        # publish the preview file
        document_id = 'hartsfield558'
        filename = '%s.xml' % document_id
        response = self.client.post(publish_url, {'preview_id': document_id}, follow=True)
        code = response.status_code
        expected = 200  # final code, after following redirects
        self.assertEqual(code, expected,
            'Expected %s but returned %s for %s (POST, following redirects) as admin user'
            % (expected, code, publish_url))
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_(reverse('fa-admin:index') in redirect_url)
        expected = 303      # redirect
        self.assertEqual(code, expected, 'Expected %s but returned %s for %s (POST) as admin user'
            % (expected, code, publish_url))

        # convert messages into an easier format to test
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

        task = TaskResult.objects.get(object_id=document_id)
        self.assert_(isinstance(task, TaskResult),
            "TaskResult was created in db for pdf reload after successful publish")

        # attempt to publish a document NOT loaded to preview
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.post(publish_url, {'preview_id': 'bogus345'}, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Publish failed. Could not retrieve' in msgs[0],
            'error message set in response context attempting to publish a document not in preview')

        # force an exist save error by setting collection to a non-existent collection
        # - load to preview for next three tests
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.post(reverse('fa-admin:preview-ead', kwargs={'archive': 'marbl'}),
                {'filename': filename})

        # publish to non-existent collection
        # - doesn't cause an error on existdb 2.2 / using rest api

        # NOTE: formerly included tests for publish invalid or badly formed xml
        # these cases are no longer possible since it is impossible
        # to load that content to preview

        # simulate incorrect eXist permissions by not specifying username/password
        # ensure guest account cannot update
        # self.db.setPermissions(settings.EXISTDB_ROOT_COLLECTION, 'other=-update')
        self.db.setPermissions(settings.EXISTDB_ROOT_COLLECTION, 0774)
        with override_settings(EXISTDB_SERVER_USER=None,
                               EXISTDB_SERVER_PASSWORD=None):
            response = self.client.post(publish_url, {'preview_id': document_id},
                follow=True)
            self.assertContains(response, "Publish failed")
            self.assertContains(response, "Could not retrieve",
                msg_prefix="error message displays explanation and instructions to user")

        # NOTE: formerly included test for exist not running, but not testable
        # because publish now requires preview database be accessible

        # test user who doesn't have permissions on the archive
        filename = 'hartsfield558.xml'
        # load to preview
        with patch('findingaids.fa.models.Archive.svn_local_path', fixture_dir):
            response = self.client.post(reverse('fa-admin:preview-ead', kwargs={'archive': 'marbl'}),
                {'filename': filename}, follow=True)

        # update user to remove marbl access
        user = User.objects.get(username=self.credentials['admin']['username'])
        marbl = Archive.objects.get(slug='marbl')
        user.archivist.archives.remove(marbl)
        user.save()
        response = self.client.post(publish_url, {'preview_id': 'hartsfield558'}, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('You do not have permission to publish' in msgs[0],
            'user should see a message if they don\'t have access to publish')

        # test archive not identified from ead (subarea/name mismatch)
        marbl.name = 'Manuscripts & Archives'
        marbl.save()
        user.archivist.archives.add(marbl)
        user.save()
        response = self.client.post(publish_url, {'preview_id': 'hartsfield558'}, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Publish failed. Could not find archive' in msgs[0],
            'user should see a message if the EAD subarea doesn\'t match a configured archive')

        # test subarea not specified in ead
        self.tmpdir = tempfile.mkdtemp('fa-publish')
        # load fixture and save elsewhere without a subarea
        ead = load_xmlobject_from_file(os.path.join(fixture_dir, 'hartsfield558.xml'),
                                       FindingAid)
        del ead.repository[0]
        with open(os.path.join(self.tmpdir, 'hartsfield558.xml'), 'w') as xmlfile:
            ead.serializeDocument(xmlfile, pretty=True)
        # load to preview
        with patch('findingaids.fa.models.Archive.svn_local_path', self.tmpdir):
            response = self.client.post(reverse('fa-admin:preview-ead', kwargs={'archive': 'marbl'}),
                {'filename': 'hartsfield558.xml'}, follow=True)
        response = self.client.post(publish_url, {'preview_id': 'hartsfield558'}, follow=True)
        msgs = [str(msg) for msg in response.context['messages']]
        self.assert_('Could not determine which archive' in msgs[0],
            'user should see an error message if the EAD has no subarea present')

