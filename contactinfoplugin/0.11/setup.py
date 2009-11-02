from setuptools import find_packages, setup

version='0.0'

setup(name='ContactInfo',
      version=version,
      description="contact information for a Trac project",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin view',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'contactinfo': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      contactinfo = contactinfo
      """,
      )

