from datetime import datetime
import glob
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulcore.django.existdb import ExistDB, ExistDBException

from findingaids.fa_admin.utils import check_ead

class Command(BaseCommand):
    """Load all or specified EAD xml files in the configured source directory
to the configured eXist collection.

If filenames are specified as arguments, only those files will be loaded.
Files should be specified by basename only (assumed to be in the configured
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
                        success = db.load(open(file, 'r'), dbpath, overwrite=True)
                        if success:
                            loaded += 1
                            if verbosity >= v_normal:
                                print "Loading %s" % file
                        else:
                            errored += 1
                            print "Error: failed to load %s to eXist" % file
                except ExistDBException, e:
                    print "Error: failed to load %s to eXist" % file
                    print e.message()
                    errored += 1

            end_time = datetime.now()
            
            # summary of what was done
            print "%d document%s loaded" % (loaded, 's' if loaded != 1 else '')
            print "%d document%s with errors" % (errored, 's' if errored != 1 else '')
            if verbosity >= v_normal:
                print "Ran for %s" % str(end_time - start_time)
            
        except Exception, err:
            raise CommandError(err)

