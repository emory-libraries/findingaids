# file findingaids/fa_admin/source.py
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

import glob
import logging
import os
import time

from subvertpy import wc

from django.shortcuts import get_object_or_404

from findingaids.fa.models import Archive
from findingaids.fa_admin.models import EadFile
from findingaids.fa_admin.svn import svn_client, svn_remote

'''
Methods to support identifying and accessing source content to be published
via the findingaids admin interface.
'''

logger = logging.getLogger(__name__)


def recent_xml_files(dir):
    '''Return recently modified xml files from a specified directory.

    :rtype: list of :class:`~findingaids.fa_admin.models.Eadfile`
    '''
    # get all xml files in the specified directory
    filenames = glob.glob(os.path.join(dir, '*.xml'))
    # modified time, base name of the file
    files = [EadFile(os.path.basename(file), os.path.getmtime(file)) for file in filenames]
    # sort by last modified time
    return sorted(files, key=lambda file: file.mtime, reverse=True)


def svn_xml_files(archive):
    # NOTE: svn client still access remote repo info instead of local working copy
    # (using the working copy is significantly faster)
    svnwc = wc.WorkingCopy(None, archive.svn_local_path)
    start = time.time()
    svn_info = svnwc.entries_read()
    logger.debug('svn read entries for %d files for %s in %f sec' %
                (len(svn_info.keys()), archive.slug, time.time() - start))

    files = []
    # for filename, info in svn_info.iteritems():
    for filename, entry in svn_info.iteritems():
        # skip non-xml content
        if not filename.endswith('.xml'):
            continue
        # svn timestamp includes microseconds and has to be divided
        # before we can treat it as a normal unix timestamp
        # https://github.com/jelmer/subvertpy/blob/f5608aa28506cfc0eb62e7a780b60f6aecb88135/subvertpy/properties.py#L50
        files.append(EadFile(filename, (entry.cmt_date / 1000000), archive))

    return files

def files_to_publish(archive):
    # determine local/remote revision to see if an update is needed
    start = time.time()
    svnwc = wc.WorkingCopy(None, archive.svn_local_path)
    # NOTE: second arg is path; first arg not documented (?!)
    local_rev = svnwc.entry(archive.svn_local_path).revision
    logger.debug('svn local revision for %s is %d (%f sec)' %
                (archive.slug, local_rev, time.time() - start))

    remote = svn_remote(archive.svn)
    start = time.time()
    latest_rev = remote.get_latest_revnum()
    logger.debug('svn remote revision for %s is %d (%f sec)' %
                (archive.slug, latest_rev, time.time() - start))

    # ONLY do an svn update if the revisions don't match
    if local_rev != latest_rev:
        svn = svn_client()
        start = time.time()
        svn.update(str(archive.svn_local_path))   # apparently can't handle unicode
        logger.debug('svn update %s in %f sec' % (archive.slug, time.time() - start))

    # return list of recent xml files from the working copy
    return svn_xml_files(archive)