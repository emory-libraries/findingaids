# This dummy django settings file is used by sphinx while loading
# eulcore.django.* to examine it for autodoc generation.

# NOTE: something being included needs eXist to be set to something valid

#Exist DB Settings
EXISTDB_SERVER_PROTOCOL = "http://"
EXISTDB_SERVER_HOST     = "kamina.library.emory.edu:8080/exist/xmlrpc"
EXISTDB_SERVER_USER     = "edc_user"
EXISTDB_SERVER_PWD      = "emory"
EXISTDB_SERVER_URL      = EXISTDB_SERVER_PROTOCOL + EXISTDB_SERVER_USER + ":" + \
    EXISTDB_SERVER_PWD + "@" + EXISTDB_SERVER_HOST
EXISTDB_ROOT_COLLECTION = "/FindingAids/emory"
EXISTDB_TEST_COLLECTION = "/fa-test"

