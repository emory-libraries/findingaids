# file findingaids/fa/context_processors.py
#
#   Copyright 2012 Emory University Library
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import findingaids
from findingaids.fa.forms import KeywordSearchForm


def searchform(request):
    "Template context processor: add the simple keyword search form to context"
    return {'kwsearch_form': KeywordSearchForm()}


def version(request):
    "Template context processor: add the findingaids software version to context."
    return { 'SW_VERSION': findingaids.__version__ }
