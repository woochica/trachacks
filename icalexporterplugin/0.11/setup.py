from setuptools import find_packages, setup

version='0.1'

setup(name='icalexporter',
      version=version,
      description="trac plugin to export the feed of an item to iCal format",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      maintainer='Olemis Lang',
      maintainer_email='olemis+trac@gmail.com',
      url='http://trac-hacks.org/wiki/IcalExporterPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=["Genshi>=0.5", "FeedParser"],
      entry_points = """
      [trac.plugins]
      icalexporter = icalexporter
      """,
      )

