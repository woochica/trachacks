from setuptools import setup

PACKAGE = 'TracSupose'
VERSION = '0.0.1'
setup(name=PACKAGE,
      version=VERSION,
      packages=['tracsupose'],
      package_data={'tracsupose' : ['templates/*.html','htdocs/css/*.css']},
      author='Bangyou Zheng',
      maintainer='Bangyou Zheng',
      maintainer_email='zheng.bangyou@gmail.com',
      description='Search SVN repository history with SupoSE',
      url="http://trac-hacks.org/wiki/TracSuposePlugin",
      license='BSD',
      scripts=['update-index'],
      entry_points = {'trac.plugins': '%s = tracsupose' % PACKAGE})
