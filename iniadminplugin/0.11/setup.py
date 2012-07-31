from setuptools import setup

setup(name='IniAdmin',
      version='0.2',
      packages=['iniadmin'],
      author='Alec Thomas',
      description='Expose all TracIni options using the Trac config option API',
      url='http://trac-hacks.org/wiki/IniAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': ['iniadmin = iniadmin']},
      package_data={'iniadmin' : ['htdocs/css/*.css', 'templates/*.html', ]},
      test_suite='iniadmin.tests',
)
