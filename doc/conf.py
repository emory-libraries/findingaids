# file doc/conf.py
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

# Finding Aids documentation build configuration file

import findingaids

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage'
]

#templates_path = ['templates']
exclude_trees = ['build']
source_suffix = '.rst'
master_doc = 'index'

project = 'Finding Aids'
copyright = '2010, Emory University Libraries'
version = '%d.%d' % findingaids.__version_info__[:2]
release = findingaids.__version__
#modindex_common_prefix = ['findingaids.']

pygments_style = 'sphinx'

html_theme = 'alabaster'
#html_static_path = ['static']
htmlhelp_basename = 'fadoc'

latex_documents = [
  ('index', 'FindingAids.tex', u'Finding Aids Documentation',
   u'EUL', 'manual'),
]

intersphinx_mapping = {'http://docs.python.org/': None}
todo_include_todos = True
