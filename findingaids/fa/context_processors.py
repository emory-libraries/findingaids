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

from django.conf import settings
import findingaids
from findingaids.fa.forms import KeywordSearchForm


def searchform(request):
    "Template context processor: add the simple keyword search form to context"
    return {'kwsearch_form': KeywordSearchForm()}


def common_settings(request):
    '''Template context processor to add selected settings to template
    context for use on any page .'''

    context_extras = {
        'SW_VERSION': findingaids.__version__,
        'ENABLE_BETA_WARNING': getattr(settings, 'ENABLE_BETA_WARNING',
                                       False),
        'DEFAULT_DAO_LINK_TEXT': getattr(settings, 'DEFAULT_DAO_LINK_TEXT',
                                         '[Resource available online]'),
        'AEON_BASE': getattr(settings, 'AEON_BASE',False)
    }
    return context_extras
