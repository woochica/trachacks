from setuptools import setup

setup(name='NavMover',
      version='0.1',
      packages=['navmover'],
      entry_points = {'trac.plugins': ['navmover = navmover']},
      package_data={'navmover' : ['htdocs/css/*.css']},
      author = 'Alec Thomas',
      description = 'A plugin for moving Trac meta navigation items into the main navigation bar.',
      license = 'BSD',
      keywords = 'trac navigation main meta',
      url = 'http://trac-hacks.org/wiki/NavMoverPlugin')
