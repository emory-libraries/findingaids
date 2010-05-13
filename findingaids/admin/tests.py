from django.test import Client
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from findingaids.admin.views import _get_recent_xml_files
import tempfile
from time import sleep
import os

class AdminViewsTest(TestCase):
    fixtures =  ['user']
    # create temporary directory with files for testing
    # (unchanged by tests, so only doing once here instead of in setup)
    tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')
    tmpfiles = []
    for num in ['first', 'second', 'third']:
        tmpfiles.append(tempfile.NamedTemporaryFile(suffix='.xml', prefix=num+'_', dir=tmpdir))
        sleep(1)        # ensure modification times are different
    # add a non-xml file
    nonxml_tmpfile = tempfile.NamedTemporaryFile(suffix='.txt', prefix='nonxml', dir=tmpdir)

    def setUp(self):
        self.client = Client()
        # tmp dir for testing source ead files
        
        # temporarily override setting for testing
        if hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
            self._stored_ead_src = settings.FINDINGAID_EAD_SOURCE
        settings.FINDINGAID_EAD_SOURCE = self.tmpdir

    def tearDown(self):
        if hasattr(self, '_stored_ead_src'):
            settings.FINDINGAID_EAD_SOURCE = self._stored_ead_src

    def test_get_recent_xml_files(self):        
        recent_xml = _get_recent_xml_files(self.tmpdir)
        filenames = [file for file, mtime in recent_xml]
        self.assertEqual(3, len(recent_xml))
        # should be in reverse order - last created first
        self.assertEqual(filenames[0], os.path.basename(self.tmpfiles[2].name))
        self.assertEqual(filenames[1], os.path.basename(self.tmpfiles[1].name))
        self.assertEqual(filenames[2], os.path.basename(self.tmpfiles[0].name))
        # non-xml file not included
        self.assert_(os.path.basename(self.nonxml_tmpfile.name) not in filenames)

        # restrict just to two - confirm only 2 are returned
        recent_xml = _get_recent_xml_files(self.tmpdir, 2)
        self.assertEqual(2, len(recent_xml))

    def test_recent_files(self):
        admin_index = reverse('admin:index')
        # note: recent files list is *currently* displayed on main admin page

        # not logged in
        response = self.client.get(admin_index)
        code = response.status_code
        expected = 302
        self.failUnlessEqual(code, expected, 'Expected %s but returned %s for %s as AnonymousUser'
                             % (expected, code, admin_index))

        # follow redirects
        response = self.client.get(admin_index, follow=True)
        (redirect_url, code) = response.redirect_chain[0]
        self.assert_("?next=%s" % admin_index in redirect_url)
        
        # log in as an admin user
        self.client.login(username='testadmin', password='secret')
        response = self.client.get(admin_index)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(3, len(response.context['files']))
        self.assert_('error' not in response.context)
        self.assertContains(response, os.path.basename(self.tmpfiles[0].name))
        self.assertContains(response, os.path.basename(self.tmpfiles[2].name))

        # simulate configuration error
        settings.FINDINGAID_EAD_SOURCE = "/does/not/exist"
        self.client.login(username='testadmin', password='secret')
        response = self.client.get(admin_index)
        self.assert_("check config file" in response.context['error'])
        self.assertEqual(0, len(response.context['files']))
        
