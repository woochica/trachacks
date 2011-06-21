from setuptools import find_packages, setup

setup(name='GroupingAssignToPlugin',
      version='0.2',
      packages=find_packages(exclude=''),
      package_data={},
      author='Patrick Schaaf',
      author_email='trachacks@bof.de',
      description='Fill Assign-To by looking at permission groups',
      url='https://trac-hacks.org/wiki/GroupingAssignToPlugin',
      license='GPLv2',
      entry_points={'trac.plugins': ['groupingassignto = groupingassignto']},
)
