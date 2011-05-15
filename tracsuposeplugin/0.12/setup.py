from setuptools import setup

setup(name='tracsupose',
      version='0.0.1',
      packages=['tracsupose'],
      package_data={'tracsupose' : [
        'templates/*.html']},
      author='Bangyou Zheng',
      maintainer='Bangyou Zheng',
      maintainer_email='zheng.bangyou@gmail.com',
      url="http://trac-hacks.org/wiki/TracSupoSE",
      license='BSD',
      scripts=['update-index'],
      entry_points = {'trac.plugins': ['tracsupose = tracsupose']})
