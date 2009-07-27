from setuptools import find_packages, setup

version='0.3'

setup(name='icalview',
      version=version,
      description="trac plugin Query as iCal format",
      author='Xavier Péchoultres',
      author_email='x.pechoulres@clariprint.com',
      url='http://www.clariprint.com',
      keywords='trac plugin icalendar',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      entry_points = """
      [trac.plugins]
      icalview = icalview
      """,
      )

