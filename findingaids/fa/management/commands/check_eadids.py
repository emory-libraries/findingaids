from django.core.management.base import BaseCommand, CommandError
from findingaids.fa.urls import EADID_URL_REGEX
from findingaids.fa.models import FindingAid
import re
 
class Command(BaseCommand):
        
    help = """Check ead id's against regular expression used in 'views.py' for ead ids."""
 
    def handle(self, *args, **options):
       
        if args and args[0] == 'help':
            print self.help
        else:
            eadids = FindingAid.objects.only('eadid').distinct()
            total = 0;
            mismatch = 0;
            regextest = re.compile(EADID_URL_REGEX)
            print "Checking the ead id against the regex '%s'" % EADID_URL_REGEX
            for ead in eadids:
                total += 1;
                if not regextest.match(ead):
                    mismatch += 1; 
                    print "'%s' does not match" % ead

            print "total records: ", total
            print "error: ", mismatch        
            return
