from setuptools import setup

setup(name='tracreposearch',
      version='0.2',
      packages=['tracreposearch'],
      author='Alec Thomas',
      maintainer='Ryan J Ollos',
      maintainer_email='ryano@physiosonics.com',
      url="http://trac-hacks.org/wiki/TracRepoSearch",
      license='BSD',
      scripts=['update-index'],
      entry_points = {'trac.plugins': ['tracreposearch = tracreposearch']})
