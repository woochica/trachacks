from setuptools import setup

PACKAGE = 'PageToDocbook'
VERSION = '0.6.3'

setup(name=PACKAGE,
      version=VERSION,
      packages=['pagetodocbook'],
      entry_points={'trac.plugins': '%s = pagetodocbook' % PACKAGE},

      package_data={'pagetodocbook': ['data/*.txt',
             'data/headingsNormalizer/*.xsl',
             'data/html2db/*']},

      # dependencies
      install_requires = ['setuptools'],

      # automatically extract everything bellow 'data'
      #eager_resources=['data'],

      #extras_require = {'tidy':['ctypes','utidylib']},

      #dependency_links=['http://cctools.svn.sourceforge.net/svnroot/cctools/vendorlibs/utidylib/#egg=utidylib-0.2-cvs',],


      # author metadata
      author = 'Filipe F. Correia',
      author_email = 'fcorreia@gmail.com',
      description = '',
      license = 'BSD',
      url = 'http://trac-hacks.org/wiki/Page2DocbookPlugin',

)

