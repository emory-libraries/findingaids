import os
import glob
from lxml.etree import XMLSyntaxError
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from eulxml.xmlmap.core import load_xmlobject_from_file
from findingaids.fa.models import FindingAid

class Command(BaseCommand):
    """Populate the top-level unitid identifier attribute with a machine-readable
numeric-only manuscript number based on the text of the unitid.

If filenames are specified as arguments, only those files will be prepared.
Files should be specified by basename only (assumed to be in the configured
EAD source directory). Otherwise, all .xml files in the configured EAD source
directory will be prepared."""
    help = __doc__

    args = '[<filename filename ... >]'
    
    help = __doc__

    # text unitid looks something like this:
    # Manuscript Collection No. 39
    # regex to extract just the numeric portion at the end
    unitid_regex = re.compile('[^\d]+(?P<number>\d+)\s*$', re.MULTILINE)

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1

        # check for required settings
        if not hasattr(settings, 'FINDINGAID_EAD_SOURCE') or not settings.FINDINGAID_EAD_SOURCE:
            raise CommandError("FINDINGAID_EAD_SOURCE setting is missing")
            return

        if verbosity > v_normal:
            print "Preparing documents from configured EAD source directory: %s" \
                    % settings.FINDINGAID_EAD_SOURCE

        updated = 0
        unchanged = 0
        errored = 0

        if len(args):
            files = [os.path.join(settings.FINDINGAID_EAD_SOURCE, name) for name in args]
        else:
            files = glob.iglob(os.path.join(settings.FINDINGAID_EAD_SOURCE, '*.xml'))

        for file in files:
            try:
                ead = load_xmlobject_from_file(file, FindingAid)
                orig_xml = ead.serializeDocument(pretty=True)
                unitid = unicode(ead.archdesc.unitid)

                match = self.unitid_regex.search(unitid)
                if not match:
                    raise Exception('Could not determine collection number for %s - %s' % \
                            (file, unitid))
                            
                collection_num = match.group('number')
                if verbosity > v_normal:
                    print "Identifier for %s is %s (%s)" % (file, collection_num, unitid)
                ead.archdesc.unitid.identifier = collection_num

                if orig_xml == ead.serializeDocument(pretty=True):
                    if verbosity > v_normal:
                        print "No changes made to %s" % file
                    unchanged += 1
                else:
                    with open(file, 'w') as f:
                        ead.serializeDocument(f, pretty=True)
                    if verbosity > v_normal:
                        print "Updated %s" % file
                    updated += 1
            except XMLSyntaxError, e:
                # xml is not well-formed
                print "Error: failed to load %s (document not well-formed XML?)" \
                            % file
                errored += 1
            except Exception, e:
                # catch any other exceptions
                print "Error: failed to set identifier for %s : %s" % (file, e)
                errored += 1

        # summary of what was done
        print "%d document%s updated" % (updated, 's' if updated != 1 else '')
        print "%d document%s unchanged" % (unchanged, 's' if unchanged != 1 else '')
        print "%d document%s with errors" % (errored, 's' if errored != 1 else '')
