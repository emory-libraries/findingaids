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

from django.conf import settings

from findingaids.fa_admin.models import EadFile
from findingaids.fa_admin.svn import svn_client

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
    svn = svn_client()
    # url, most recent revision, depth 1
    svn_list = svn.list(archive.svn_local_path, 'HEAD', 1)
    files = []
    for filename, info in svn_list.iteritems():
        # skip non-xml content
        if not filename.endswith('.xml'):
            continue
        # svn timestamp includes microseconds and has to be divided
        # before we can treat it as a normal unix timestamp
        # https://github.com/jelmer/subvertpy/blob/f5608aa28506cfc0eb62e7a780b60f6aecb88135/subvertpy/properties.py#L50
        files.append(EadFile(filename, (info['time'] / 1000000), archive))

    return files

def files_to_publish(archives=[]):

    if archives:
        # only handle the first archive for now
        archive = archives[0]
        svn = svn_client()
        # update to make sure we have latest version of everything
        svn.update(str(archive.svn_local_path))   # apparently can't handle unicode
        # returns a list of revisions
        # NOTE: might be nice to log current revision if we know it has changed
        # return list of recent xml files from the svn
        return svn_xml_files(archive)

    # NOTE: trying to preserve fall-back behavior that allows publication
    # from a single configured directory; however, as the admin
    # page changes this may be difficult to maintain

    if not hasattr(settings, 'FINDINGAID_EAD_SOURCE'):
        raise Exception('Please configure EAD source directory in local settings.')
    else:
        dir = settings.FINDINGAID_EAD_SOURCE
        if os.access(dir, os.F_OK | os.R_OK):
            return recent_xml_files(dir)
        else:
            msg = '''EAD source directory '%s' does not exist or is
            not readable; please check config file.''' % dir
            raise Exception(msg)
