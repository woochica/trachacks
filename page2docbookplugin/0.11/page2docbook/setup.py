from setuptools import setup

PACKAGE = 'PageToDocbook'
VERSION = '0.6'

setup(name=PACKAGE,
      version=VERSION,
      packages=['pagetodocbook'],
      entry_points={'trac.plugins': '%s = pagetodocbook' % PACKAGE},

      package_data={'pagetodocbook': ['data/*.*']},

      # dependencies
      install_requires = ['setuptools',
                          ],

      #extras_require = {'tidy':['ctypes','utidylib']},

      #dependency_links=['http://cctools.svn.sourceforge.net/svnroot/cctools/vendorlibs/utidylib/#egg=utidylib-0.2-cvs',],

      # author metadata
      author = 'Filipe F. Correia',
      author_email = 'fcorreia@gmail.com',
)

