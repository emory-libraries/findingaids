# file doc/doc_djangosettings.py
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

# This dummy django settings file is used by sphinx while loading
# findingaids.* to examine it for autodoc generation.

# NOTE: something being included needs eXist to be set to something valid
EXISTDB_SERVER_URL      = 'http://edc_user:emory@kamina.library.emory.edu:8080/exist/xmlrpc'
EXISTDB_ROOT_COLLECTION = "/FindingAids/emory"
EXISTDB_TEST_COLLECTION = "/fa-test"
