import glob
from lxml.etree import XMLSyntaxError
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from eulcore.django.existdb import ExistDB
from eulcore.xmlmap.core import load_xmlobject_from_file

from findingaids.fa.models import FindingAid
from findingaids.fa_admin.utils import clean_ead, check_ead

class Command(BaseCommand):
    help = """Clean all or specified EAD xml files in the configured source directory.

Runs EAD xml files through a "cleaning" process to set ids, etc., as needed
to be published, verifies that the resulting EAD is valid and passes all
checks, and if so, updates the original file with the new, cleaned EAD xml.

If filenames are specified as arguments, only those files will be cleaned.
Files should be specified by basename only (assumed to be in the configured
EAD source directory). Otherwise, all .xml files in the configured EAD source
directory will be cleaned."""

    args = '[<filename filename ... >]'
    
    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        
        # check for required settings
        if not hasattr(settings, 'EXISTDB_ROOT_COLLECTION') or not settings.EXISTDB_ROOT_COLLECTION:
            raise CommandError("EXISTDB_ROOT_COLLECTION setting is missing")
            return
        if not hasattr(settings, 'FINDINGAID_EAD_SOURCE') or not settings.FINDINGAID_EAD_SOURCE:
            raise CommandError("FINDINGAID_EAD_SOURCE setting is missing")
            return

        updated = 0
        unchanged = 0
        errored = 0
        try:
            if len(args):
                files = [os.path.join(settings.FINDINGAID_EAD_SOURCE, name) for name in args]
            else:
                files = glob.iglob(os.path.join(settings.FINDINGAID_EAD_SOURCE, '*.xml'))
                self.db = ExistDB()


            for file in files:
                try:
                    ead = load_xmlobject_from_file(file, FindingAid)
                    orig_xml = ead.serialize(pretty=True)
                    ead = clean_ead(ead, file)
                    # sanity check before saving
                    dbpath = settings.EXISTDB_ROOT_COLLECTION + "/" + os.path.basename(file)
                    # FIXME: DTD validation is an issue here (no longer file, not on path...)
                    errors = check_ead(file, dbpath, xml=ead.serialize())
                    if errors:
                        errored += 1                        
                        print "Cleaned EAD for %s does not pass sanity checks, not saving." % file
                        if verbosity >= v_normal:
                            print "  Errors found:"
                            for err in errors:
                                print "    %s" % err
                    elif orig_xml == ead.serialize(pretty=True):
                        if verbosity >= v_normal:
                            print "No changes made to %s" % file
                        unchanged += 1
                    else:
                        with open(file, 'w') as f:
                            ead.serialize(f, pretty=True)
                        if verbosity >= v_normal:
                            print "Updated %s" % file
                        updated += 1
                except XMLSyntaxError, e:
                    # xml is not well-formed
                    print "Error: failed to load %s (document not well-formed XML?)" \
                                % file
                    errored += 1

            # summary of what was done
            print "%d document%s updated" % (updated, 's' if updated != 1 else '')
            print "%d document%s unchanged" % (unchanged, 's' if unchanged != 1 else '')
            print "%d document%s with errors" % (errored, 's' if errored != 1 else '')
            
        except Exception, err:
            raise CommandError(err)

