from setuptools import setup

PACKAGE = 'TracSVNHooks'
VERSION = '0.4'

setup(
    name = PACKAGE,
    version = VERSION,
    author = "Robert Barsch",
    author_email = "barsch@lmu.de",
    description = "A interface to edit SVN repository hooks via admin panel",
    license = "BSD",
    keywords = "trac plugin SVN hooks",
    url = "http://svn.geophysik.uni-muenchen.de/trac/tracmods/",
    classifiers = ['Framework :: Trac',],
    install_requires = ['TracWebAdmin'],
    packages = ['svnhooks'],
    entry_points = {'trac.plugins': '%s = svnhooks' % PACKAGE},
    package_data = {'svnhooks': ['templates/*.cs']},
)
          