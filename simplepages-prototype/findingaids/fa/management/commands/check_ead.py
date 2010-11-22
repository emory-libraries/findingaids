import re
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from findingaids.fa.urls import EADID_URL_REGEX, TITLE_LETTERS
from findingaids.fa.models import FindingAid
 
class Command(BaseCommand):        
    """Check the specified field in all Finding Aids loaded in the configured
eXist collection against the regular expressions used for URLs in the site,
and reports on any documents that fail.

If ``eadid`` is specified, checks that each eadid matches the regular expression
in the single document URL pattern.

If ``title`` is specified, checks that the first letter of the list title is
included in the allowed first-letters for the browse URL.
"""
    help = __doc__
 
    _args = ['eadid', 'title']
    args = ' | '.join(_args)

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])    # 1 = normal, 0 = minimal, 2 = all
        v_normal = 1
        v_all = 2

        if not len(args):
            print "A command is required; please choose one of the following: %s\n" \
                    % ' '.join(self._args)
            print self.help
            return

        cmd = args[0]
        if cmd not in self._args:
            print "Command '%s' not recognized\n" % cmd
            print self.help
            return

        # check for required settings
        if not hasattr(settings, 'EXISTDB_ROOT_COLLECTION') or not settings.EXISTDB_ROOT_COLLECTION:
            raise CommandError("EXISTDB_ROOT_COLLECTION setting is missing")
            return

        if verbosity == v_all:
            print 'Checking documents in configured eXist collection: %s' \
                    % settings.EXISTDB_ROOT_COLLECTION

        if cmd == 'eadid':
            eadids = FindingAid.objects.only('eadid').distinct()
            mismatch = 0
            regextest = re.compile(EADID_URL_REGEX)
            if verbosity == v_all:
                print "Checking each eadid against the regex '%s'" % EADID_URL_REGEX
            for ead in eadids:
                if verbosity == v_all:
                    print "Checking %s" % ead
                if not regextest.match(ead):
                    mismatch += 1
                    print "Error: '%s' does not match" % ead

            print "Checked %s record%s" % (eadids.count(), 's' if eadids.count() != 1 else '')
            print "%s error%s" % (mismatch, 's' if mismatch != 1 else '')

        elif cmd == 'title':
            if verbosity == v_all:
                print "Checking titles"

            fas = FindingAid.objects.only('document_name', 'eadid', 'first_letter',
                    'list_title').order_by('first_letter')
            mismatch = 0
            regextest = re.compile(TITLE_LETTERS)
            if verbosity == v_all:
                print "Checking list title first letters against the regex '%s'" % TITLE_LETTERS
            for fa in fas:
                if verbosity == v_all:
                    print "Checking %s - '%s'" % (fa.eadid, fa.first_letter)
                try:
                    if not regextest.match(unicode(fa.first_letter)):
                        mismatch += 1
                        print "Error: document %s does not match regex. First letter is '%s'." \
                                % (fa.document_name, fa.first_letter)
                except Exception, e:
                    print "Error testing first letter for %s: " % fa.document_name, e

            print "Checked %s record%s" % (fas.count(), 's' if fas.count() != 1 else '')
            print "%s error%s" % (mismatch, 's' if mismatch != 1 else '')

