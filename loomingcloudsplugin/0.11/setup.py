from setuptools import find_packages, setup

version='0.1'

setup(name='LoomingClouds',
      version=version,
      description="inline clouds for ticket.html",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['TracTags'],
      dependency_links=['http://trac-hacks.org/svn/tagsplugin/tags/0.6#egg=TracTags'],
      entry_points = """
      [trac.plugins]
      loomingclouds = loomingclouds
      """,
      )

