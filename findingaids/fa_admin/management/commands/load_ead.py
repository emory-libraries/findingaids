from datetime import datetime
import glob
import os
import sys
from time import sleep

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulcore.xmlmap.core import load_xmlobject_from_file
from eulcore.django.existdb import ExistDB, ExistDBException

from findingaids.fa.models import FindingAid
from findingaids.fa_admin.utils import check_ead
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

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        v_all = 2

        # check for required settings
        if not hasattr(settings, 'EXISTDB_ROOT_COLLECTION') or not settings.EXISTDB_ROOT_COLLECTION:
            raise CommandError("EXISTDB_ROOT_COLLECTION setting is missing")
            return
        if not hasattr(settings, 'FINDINGAID_EAD_SOURCE') or not settings.FINDINGAID_EAD_SOURCE:
            raise CommandError("FINDINGAID_EAD_SOURCE setting is missing")
            return

        if verbosity == v_all:
            print "Loading documents from configured EAD source directory: %s" \
                    % settings.FINDINGAID_EAD_SOURCE
            print 'Documents will be loaded to configured eXist collection: %s' \
                    % settings.EXISTDB_ROOT_COLLECTION
        db = ExistDB()

        loaded = 0
        errored = 0
        pdf_tasks = {}

        start_time = datetime.now()
        try:
            if len(args):
                files = [os.path.join(settings.FINDINGAID_EAD_SOURCE, name) for name in args]
            else:
                files = glob.iglob(os.path.join(settings.FINDINGAID_EAD_SOURCE, '*.xml'))
                self.db = ExistDB()

            for file in files:
                try:                    
                    # full path location where file will be loaded in exist db collection
                    dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + os.path.basename(file)
                    errors = check_ead(file, dbpath)
                    if errors:
                        # report errors, don't load
                        errored += 1
                        print "Error: document %s does not pass publication checks; not loading to eXist." % file
                        if verbosity >= v_normal:
                            print "  Errors found:"
                            for err in errors:
                                print "    %s" % err                        
                    else:
                        with open(file, 'r') as eadfile:
                            success = db.load(eadfile, dbpath, overwrite=True)
                        
                        if success:
                            loaded += 1
                            if verbosity >= v_normal:
                                print "Loaded %s" % file
                            # load the file as a FindingAid object to get the eadid for PDF reload
                            ead = load_xmlobject_from_file(file, FindingAid)
                            # trigger PDF regeneration in the cache and store task result
                            pdf_tasks[ead.eadid] = reload_cached_pdf.delay(ead.eadid)
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
            
        except Exception, err:
            raise CommandError(err)


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