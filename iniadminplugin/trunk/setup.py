from setuptools import setup

setup(name='IniAdmin',
      version='0.1',
      packages=['iniadmin'],
      author='Alec Thomas',
      description='Expose all TracIni options using the Trac 0.10 config option API',
      url='http://trac-hacks.org/wiki/IniAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': ['iniadmin = iniadmin']},
      install_requires=['TracWebAdmin'])
