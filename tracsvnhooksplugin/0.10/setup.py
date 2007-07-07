from setuptools import setup

PACKAGE = 'TracSVNHooks'
VERSION = '0.2'

setup(
  name = PACKAGE,
  version = VERSION,
  author = "Robert Barsch",
  author_email = "barsch@lmu.de",
  description = "A interface to edit SVN repository hooks via admin panel",
  license = "BSD",
  keywords = "trac plugin SVN hooks",
  url = "http://trac-hacks.org/wiki/TracSvnHooksPlugin",
  classifiers = [ 'Framework :: Trac', ],
  install_requires = ['TracWebAdmin'],
  packages=['svnhooks'],
  entry_points={'trac.plugins': '%s = svnhooks' % PACKAGE},
  package_data={'svnhooks': ['htdocs/js/*.js','htdocs/css/*.css', 'htdocs/images/*.jpg', 'templates/*.cs']},
)
		  