# file findingaids/fa_admin/management/commands/prep_ead.py
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

import glob
import logging
from lxml.etree import XMLSyntaxError
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulexistdb.db import ExistDB
from eulxml.xmlmap.core import load_xmlobject_from_file

from findingaids.fa.models import FindingAid, Archive
from findingaids.fa_admin import utils
from findingaids.fa_admin.svn import svn_client

class Command(BaseCommand):
    """Prepare all or specified EAD xml files in the configured source directory.

Runs EAD xml files through a prep process to set ids, etc., as needed
to be published, verifies that the resulting EAD is valid and passes all
checks, and if so, updates the original file with the new, prepared EAD xml.

If filenames are specified as arguments, only those files will be prepared.
Files should be specified by full path. Otherwise, all .xml files in each of
the defined Archives will be prepared."""
    help = __doc__

    args = '[<filename filename ... >]'

    # django default verbosity level options --  1 = normal, 0 = minimal, 2 = all
    v_normal = 1
    v_all = 2

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])

        self._setup_logging(verbosity)

        # check for required settings
        if not hasattr(settings, 'EXISTDB_ROOT_COLLECTION') or not settings.EXISTDB_ROOT_COLLECTION:
            raise CommandError("EXISTDB_ROOT_COLLECTION setting is missing")
            return


        if verbosity == self.v_all:
            print "Preparing documents from all defined Archives"

        updated = 0
        unchanged = 0
        errored = 0

        if len(args):
            files = args
        else:
            files = set()
            svn = svn_client()
            for archive in Archive.objects.all():
                # update to make sure we have latest version of everything
                svn.update(str(archive.svn_local_path))   # apparently can't handle unicode
                files.update(set(glob.iglob(os.path.join(archive.svn_local_path, '*.xml'))))

        for file in files:
            try:
                ead = load_xmlobject_from_file(file, FindingAid)
                orig_xml = ead.serializeDocument(pretty=True)
                ead = utils.prep_ead(ead, file)
                # sanity check before saving
                dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + os.path.basename(file)
                errors = utils.check_ead(file, dbpath, xml=ead.serializeDocument())
                if errors:
                    errored += 1
                    print "Prepared EAD for %s does not pass sanity checks, not saving." % file
                    if verbosity >= self.v_normal:
                        print "Errors found:"
                        for err in errors:
                            # some errors include a list of error instances - display nicely
                            if isinstance(err, list):
                                for suberr in err:
                                    print "    %s" % suberr
                            else:
                                print "  %s" % err
                elif orig_xml == ead.serializeDocument(pretty=True):
                    if verbosity >= self.v_normal:
                        print "No changes made to %s" % file
                    unchanged += 1
                else:
                    with open(file, 'w') as f:
                        ead.serializeDocument(f, pretty=True)
                    if verbosity >= self.v_normal:
                        print "Updated %s" % file
                    updated += 1
            except XMLSyntaxError, e:
                # xml is not well-formed
                print "Error: failed to load %s (document not well-formed XML?)" \
                            % file
                errored += 1
            except Exception, e:
                # catch any other exceptions
                print "Error: failed to prep %s : %s" % (file, e)
                errored += 1

        # summary of what was done
        print "%d document%s updated" % (updated, 's' if updated != 1 else '')
        print "%d document%s unchanged" % (unchanged, 's' if unchanged != 1 else '')
        print "%d document%s with errors" % (errored, 's' if errored != 1 else '')

        # remove the local log handler
        self.logger.removeHandler(self._sh)


    def _setup_logging(self, verbosity):
        # generate ark method logs warnings & info if existing ARKs are found
        # make sure they are displayed, as appropriate to verbosity setting

        # If default logger is configured to output to console and level is info
        # or warning, these may be double-logged...
        # not aware of any good solution to that problem
        self.logger = logging.getLogger('findingaids.fa_admin.utils')
        self._sh = logging.StreamHandler()
        self._sh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        if verbosity >= self.v_normal:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)
        self.logger.addHandler(self._sh)
