from setuptools import setup

PACKAGE = 'PageToDocbook'
VERSION = '0.5'

setup(name=PACKAGE,
      version=VERSION,
      packages=['pagetodocbook'],
      entry_points={'trac.plugins': '%s = pagetodocbook' % PACKAGE},
      package_data={'pagetodocbook': ['data/*.*']},
)

