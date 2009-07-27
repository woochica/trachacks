from setuptools import find_packages, setup

version='0.4'

setup(name='icalview',
      version=version,
      description="Provide icalendar export for Queries",
      author='Xavier Péchoultres',
      author_email='x.pechoulres@clariprint.com',
      url='http://trac-hacks.org/wiki/IcalViewPlugin',
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

