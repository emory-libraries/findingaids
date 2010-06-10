import findingaids
from findingaids.fa.forms import KeywordSearchForm

def searchform(request):
    "Template context processor: add the simple keyword search form to context"
    return {'kwsearch_form': KeywordSearchForm()}

def version(request):
    "Template context processor: add the findingaids software version to context."
    return { 'SW_VERSION': findingaids.__version__ }
