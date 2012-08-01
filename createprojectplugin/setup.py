from setuptools import setup

setup(name='CreateProj',
      version='0.1',
      packages=['createproj'],
      author='linetor based on IniAdmin by Alec Thomas',
      description='Provide a web interface for creating new projects',
      url='',
      license='BSD or any license with an equivalent disclaimer',
      entry_points={'trac.plugins': ['createproj = createproj']},
      package_data={'createproj' : ['htdocs/css/*.css', 'templates/*.cs', ]},
      install_requires=['TracWebAdmin'])
