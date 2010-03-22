from findingaids.fa.forms import KeywordSearchForm

def searchform(request):
    "Template context processor: add the simple keyword search form to context"
    return {'form': KeywordSearchForm()}
