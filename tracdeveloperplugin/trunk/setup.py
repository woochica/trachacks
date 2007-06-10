from setuptools import setup

setup(name='TracDeveloper',
      version='0.1',
      packages=['tracdeveloper'],
      author='Alec Thomas',
      description='Adds some features to Trac that are useful for developers',
      url='http://trac-hacks.org/wiki/TracDeveloperPlugin',
      license='BSD',
      entry_points={'trac.plugins': ['tracdeveloper = tracdeveloper']},
      package_data={'tracdeveloper' : ['templates/*.html', ]})
