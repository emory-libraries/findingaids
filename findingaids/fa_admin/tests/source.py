# file findingaids/fa_admin/tests/source.py
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

import os
import shutil
import tempfile
import time

from django.test import TestCase
from django.test.utils import override_settings
from mock import patch

from findingaids.fa.models import Archive
from findingaids.fa_admin.models import EadFile
from findingaids.fa_admin.source import recent_xml_files, svn_xml_files, \
    files_to_publish


class RecentXmlFilesTest(TestCase):
    # tests for view helper functions

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')
        # create xml files to list
        self.tmpfiles = []
        for num in ['first', 'second', 'third']:
            self.tmpfiles.append(tempfile.NamedTemporaryFile(suffix='.xml',
                    prefix=num + '_', dir=self.tmpdir, delete=False))
            time.sleep(1)        # ensure modification times are different
        # add a non-xml file
        self.nonxml_tmpfile = tempfile.NamedTemporaryFile(suffix='.txt',
                    prefix='nonxml', dir=self.tmpdir, delete=False)

    def tearDown(self):
        # clean up temp files & dir
        shutil.rmtree(self.tmpdir)

    def test_recent_xml_files(self):
        recent_xml = recent_xml_files(self.tmpdir)
        self.assertEqual(3, len(recent_xml))
        # should be in reverse order - last created first
        self.assertEqual(recent_xml[0].filename, os.path.basename(self.tmpfiles[2].name))
        self.assertEqual(recent_xml[1].filename, os.path.basename(self.tmpfiles[1].name))
        self.assertEqual(recent_xml[2].filename, os.path.basename(self.tmpfiles[0].name))
        # non-xml file not included
        filenames = [eadfile.filename for eadfile in recent_xml]
        self.assert_(os.path.basename(self.nonxml_tmpfile.name) not in filenames)


class SvnXmlFilesTest(TestCase):

    @patch('findingaids.fa_admin.source.svn_client')
    def test_svn_xml_files(self, mocksvnclient):
        arch = Archive(label='Test', name='Test Archives and Collections',
            svn='http://svn.example.com/test/trunk', slug='test')

        now = time.time()
        earlier = now - 300
        earliest = now - 1500
        xml_info = {
            'now.xml': {'time': now * 1000000},
            'earliest.xml': {'time': earliest * 1000000},
            'earlier.xml': {'time': earlier * 1000000}
        }
        info = xml_info.copy()
        info['nonxml.txt'] =  {'time': now * 1000000}
        mocksvnclient.return_value.list.return_value = info
        files = svn_xml_files(arch)
        mocksvnclient.return_value.list.assert_called_with(arch.svn_local_path, 'HEAD', 1)
        # should consist of all xml files in svn info
        self.assertEqual(len(xml_info.keys()), len(files))
        self.assert_(isinstance(files[0], EadFile))
        eadfile_names = [f.filename for f in files]
        self.assertEqual(xml_info.keys(), eadfile_names)
        # non .xml files should be skipped
        self.assert_('nonxml.txt' not in eadfile_names)


class FilesToPublishTest(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp('findingaids-recentfiles-test')

    def tearDown(self):
        # clean up temp files & dir
        shutil.rmtree(self.tmpdir)

    @patch('findingaids.fa_admin.source.svn_client')
    @patch('findingaids.fa_admin.source.svn_xml_files')
    def test_files_to_publish(self, mocksvnfiles, mocksvnclient):
        arch = Archive(label='Test', name='Test Archives and Collections',
            svn='http://svn.example.com/test/trunk', slug='test')

        mocksvnfiles.return_value = ['file1', 'file2']  # not reflective of actual result
        result = files_to_publish(arch)
        mocksvnclient.return_value.update.assert_called_with(arch.svn_local_path)
        mocksvnfiles.assert_called_with(arch)
        self.assertEqual(mocksvnfiles.return_value, result)

        # fallback logic
        # NOTE: not sure how to simulate setting not present with override/patch
        with override_settings(FINDINGAID_EAD_SOURCE='/tmp/not/really/there'):
            self.assertRaises(Exception, files_to_publish)

        with override_settings(FINDINGAID_EAD_SOURCE=self.tmpdir):
            with patch('findingaids.fa_admin.source.recent_xml_files') as mockrecent:
                mockrecent.return_value = ['one', 'two', 'three']
                result = files_to_publish()
                self.assertEqual(result, mockrecent.return_value)
                mockrecent.assert_called_with(self.tmpdir)


