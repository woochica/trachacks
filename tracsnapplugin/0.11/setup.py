from setuptools import setup

PACKAGE = 'TracSocialnetwork'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['socialnetwork'],
      package_data={PACKAGE: ['htdocs/*', 'templates/*']},
      entry_points={'trac.plugins': '%s = socialnetwork' % PACKAGE},
)
