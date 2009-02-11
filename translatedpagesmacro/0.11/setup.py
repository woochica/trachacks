from setuptools import setup

PACKAGE = 'TranslatedPages'
VERSION = '0.2'

setup(name=PACKAGE,
      version=VERSION,
      packages=['translatedpages'],
      entry_points={'trac.plugins': '%s = translatedpages' % PACKAGE},
#      package_data={'helloworld': ['htdocs/css/*.css', 'htdocs/images/*.jpg',
#                                   'templates/*.cs']},
)
