import sys
from django.conf import settings
from eulexistdb import db, testutil


class ExistDBSetUp(testutil.ExistDBSetUp):
    '''Extend :class:`eulexistdb.testutil.ExistDBSetUp` Nose plugin
    to also ensure that preview collection is present and available for
    testing.
    '''

    def begin(self):
        super(ExistDBSetUp, self).begin()
        # NOTE: could add logic to swap real and test preview collections
        # here (as existdb does for main collection config), or
        # to check that preview collection path starts with /test
        print >> sys.stderr, "Ensuring eXist preview collection is present: %s" % \
            settings.EXISTDB_PREVIEW_COLLECTION
        existdb = db.ExistDB()
        # create preview collection (but don't complain if it already exists)
        existdb.createCollection(settings.EXISTDB_PREVIEW_COLLECTION, True)
