from setuptools import find_packages, setup

version='0.1.2'

setup(name='svnsyncplugin',
      version=version,
      description="sets up trac access to a remote repository via svnsync",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/SvnsyncPlugin',
      keywords='trac plugin svn',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      svnsyncplugin = svnsyncplugin
      """,
      )

