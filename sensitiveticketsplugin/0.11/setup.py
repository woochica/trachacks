from setuptools import find_packages, setup

version='0.0'

setup(name='sensitivetickets',
      version=version,
      description="A plugin that lets you mark tickets as 'sensitive' with a check box.  Those tickets can only be seen with permission.",
      author='Legion',
      author_email='jhammel@openplans.org',
      url='topp.openplans.org',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'sensitivetickets': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      sensitivetickets = sensitivetickets
      """,
      )

