# file findingaids/fa_admin/management/commands/load_ead.py
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

from datetime import datetime
import glob
from optparse import make_option
import os
import sys
from time import sleep

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulxml.xmlmap.core import load_xmlobject_from_file
from eulexistdb.db import ExistDB, ExistDBException

from findingaids.fa.models import FindingAid, Archive
from findingaids.fa_admin.utils import check_ead
from findingaids.fa_admin.svn import svn_client
from findingaids.fa_admin.tasks import reload_cached_pdf


class Command(BaseCommand):
    """Load all or specified EAD xml files in the configured source directory
to the configured eXist collection.  For each document successfully loaded to
eXist, this script will trigger a celery task to reload the PDF in the cache; the
script will not exit until all tasks have completed.

If filenames are specified as arguments, only those files will be loaded.
Files should be specified by basename only (they will be loaded from the configured
EAD source directory). Otherwise, all .xml files in the configured EAD source
directory will be loaded."""
    help = __doc__

    args = '[<filename filename ... >]'

    def add_arguments(self, parser):
        parser.add_argument('--skip-pdf-reload', '-s',
            action='store_true',
            dest='skip_pdf_reload',
            help='Skip reloading PDFs in the cache.')
        parser.add_argument('--pdf-only', '-p',
            action='store_true',
            dest='pdf_only',
            help='Only reload PDFs in the cache; do not load EAD files to eXist.')


    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        v_all = 2

        if options['pdf_only'] and options['skip_pdf_reload']:
            raise CommandError("Options -s and -p are not compatible")

        # check for required settings
        if not hasattr(settings, 'EXISTDB_ROOT_COLLECTION') or not settings.EXISTDB_ROOT_COLLECTION:
            raise CommandError("EXISTDB_ROOT_COLLECTION setting is missing")
            return

        if len(args):
            files = args
        else:
            # Note: copied from prep_ead manage command; move somewhere common?
            files = set()
            svn = svn_client()
            for archive in Archive.objects.all():
                # update to make sure we have latest version of everything
                svn.update(str(archive.svn_local_path))   # apparently can't handle unicode
                files.update(set(glob.iglob(os.path.join(archive.svn_local_path, '*.xml'))))

        if verbosity == v_all:
            print 'Documents will be loaded to configured eXist collection: %s' \
                    % settings.EXISTDB_ROOT_COLLECTION
            if options['skip_pdf_reload']:
                print "** Skipping PDFs cache reload"

        db = ExistDB()

        loaded = 0
        errored = 0
        pdf_tasks = {}

        start_time = datetime.now()

        if not options['pdf_only']:
        # unless PDF reload only has been specified, load files

            for file in files:
                try:
                    # full path location where file will be loaded in exist db collection
                    dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + os.path.basename(file)
                    errors = check_ead(file, dbpath)
                    if errors:
                        # report errors, don't load
                        errored += 1
                        print "Error: %s does not pass publication checks; not loading to eXist." % file
                        if verbosity >= v_normal:
                            print "  Errors found:"
                            for err in errors:
                                print "    %s" % err
                    else:
                        with open(file, 'r') as eadfile:
                            success = db.load(eadfile, dbpath)

                        if success:
                            loaded += 1
                            if verbosity >= v_normal:
                                print "Loaded %s" % file
                            # load the file as a FindingAid object to get the eadid for PDF reload
                            ead = load_xmlobject_from_file(file, FindingAid)

                            # trigger PDF regeneration in the cache and store task result
                            # - unless user has requested PDF reload be skipped
                            if not options['skip_pdf_reload']:
                                pdf_tasks[ead.eadid.value] = reload_cached_pdf.delay(ead.eadid.value)
                                # NOTE: unlike the web admin publish, this does not
                                # generate TaskResult db records; task outcomes will be
                                # checked & reported before the script finishes
                        else:
                            errored += 1
                            print "Error: failed to load %s to eXist" % file
                except ExistDBException, e:
                    print "Error: failed to load %s to eXist" % file
                    print e.message()
                    errored += 1

            # output a summary of what was done
            print "%d document%s loaded" % (loaded, 's' if loaded != 1 else '')
            print "%d document%s with errors" % (errored, 's' if errored != 1 else '')

        # only PDF cache reloading requested
        if options['pdf_only']:
            findingaids = FindingAid.objects.all()
            for ead in findingaids:
                if verbosity > v_normal:
                     print "Queuing PDF request for %s" % ead.eadid.value
                pdf_tasks[ead.eadid.value] = reload_cached_pdf.delay(ead.eadid.value)

        if not options['skip_pdf_reload']:
            # check on the status of PDF cache reload tasks and wait until they all finish
            success, failed, pending = check_tasks(pdf_tasks)
            msg = ''
            while pending:
                if verbosity >= v_normal:
                    # back up the length of the last message so it can be overwritten
                    for i in range(len(msg)):
                        sys.stdout.write('\r')
                    msg = "Waiting for %d PDF cache reload task%s to complete..." % \
                            (len(pending), 's' if len(pending) != 1 else '')
                    sys.stdout.write(msg)
                    sys.stdout.flush()
                sleep(5)
                # check the remaining incomplete tasks, updating success/failure lists
                s, f, pending = check_tasks(pending)
                success.update(s)
                failed.update(f)

            if verbosity >= v_normal:
                # remove any last pending output message
                for i in range(len(msg)):
                    sys.stdout.write('\r')
                print ''    # print a newline after any pending output

            print "Successfully reloaded PDFs for %d document%s" % \
                    (len(success), 's' if len(success) != 1 else '')
            if verbosity >= v_all:
                print ', '.join(success.keys())
            print "Failed to reloaded PDFs for %d document%s" % \
                    (len(failed), 's' if len(failed) != 1 else '')
            print ', '.join(failed.keys())

        end_time = datetime.now()
        if verbosity >= v_normal:
            print "Ran for %s" % str(end_time - start_time)



def check_tasks(tasks):
    """Check the status of celery tasks for successful completion.  Expects
    a dictionary with values that are instances of :class:`celery.result.AsyncResult`.

    :returns: three dictionaries with the same keys and AsyncResult values as the
        input parameter, in this order: succeeded (task finished successfully),
        failed (task finished unsuccessfully), and pending (task not yet finished)
    """
    succeeded = {}
    failed = {}
    pending = {}
    for id, task in tasks.iteritems():
        if task.ready():        # task has finished running
            if task.successful():  # SUCCESS
                succeeded[id] = task
            else:   # FAILURE
                failed[id] = task
        else:   # not yet finished
            pending[id] = task
    return succeeded, failed, pending
