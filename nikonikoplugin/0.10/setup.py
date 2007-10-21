from setuptools import setup

PACKAGE = 'NikoNiko'
VERSION = '00.01.10' # the last two decimals are meant to signify the Trac version

setup(name=PACKAGE,
      description='Plugin to provide a NikoNiko page in Trac.',
      keywords='trac plugin nikoniko',
      author='Brett Smith and Majid Latif',
      license='GPL',
      url='http://3sp.com/labs',
      version=VERSION,
      packages=['nikoniko'],
      package_data={'nikoniko' : ['htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.png' ,'templates/*.cs']},
      entry_points={'trac.plugins': '%s = nikoniko ' % PACKAGE},
)
