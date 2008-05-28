from setuptools import find_packages, setup

version='0.0'

setup(name='svnsyncplugin',
      version=version,
      description="sets up trac access to a remote repository via svnsync",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://www.openplans.org',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      svnsyncplugin = svnsyncplugin
      """,
      )

