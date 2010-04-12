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

#html_theme = 'default'
#html_static_path = ['static']
htmlhelp_basename = 'fadoc'

latex_documents = [
  ('index', 'FindingAids.tex', u'Finding Aids Documentation',
   u'EUL', 'manual'),
]

intersphinx_mapping = {'http://docs.python.org/': None}
todo_include_todos = True
