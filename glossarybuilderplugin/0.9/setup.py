from setuptools import find_packages, setup

from setuptools import setup

PACKAGE = 'TracGlossary'
VERSION = '0.2'

setup(
  name          = PACKAGE,
  version       = VERSION,
  author        = 'Simon Drabble',
  author_email  = 'tracplugins@thebigmachine.org',
  license       = 'GPL',
  keywords      = 'trac plugin wiki glossary index builder',
  description   = 'Automatic glossary index builder for Trac',
  long_description = """
  This trac plug-in provides for a way to build a glossary with
  automatic index creation/ update. A a term is added to the
  glossary (by default, any page under 'Glossary/'), an link
  to it is also added to the index (by default, Glossary/Index).

  Page deletions are also tracked and handled, with links being
  removed from the index.

  Each of the various items defining the glossary (root name,
  index page name, etc) are customisable through the trac
  config file.

  Examples:

  1. A new site with no glossary entries. As entries are created
  under 'Glossary/' (for example, 'Glossary/Wiki'), a link
  is added to the Glossary/Index page. A link to the index
  itself is also added to the Glossary/Wiki page.

  2. An existing site with glossary entries under 'Terms/'.
  Edit the trac conf file to define:

  [glossary]
  prefix = Terms
  
  Edit any of the Terms/* pages. 'Terms/Index' will be
  created, but empty. Click the 'rebuild' link on the
  Index page and it will be populated with all pages under
  'Terms/'
  """,
  platform      = 'Any',
  packages      = ['glossary'],
  entry_points  = { 'trac.plugins': '%s = glossary' % PACKAGE },
)
