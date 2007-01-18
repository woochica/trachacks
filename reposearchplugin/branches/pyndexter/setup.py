from setuptools import setup

setup(name='tracreposearch',
      version='0.3',
      packages=['tracreposearch'],
      author='Alec Thomas',
      url="http://trac-hacks.org/wiki/TracRepoSearch",
      license='BSD',
      scripts=['update-index'],
      entry_points = {'trac.plugins': ['tracreposearch = tracreposearch']})
