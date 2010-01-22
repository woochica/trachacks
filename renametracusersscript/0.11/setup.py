from setuptools import find_packages, setup

version='0.2'

setup(name='RenameTracUsers',
      version=version,
      description="rename the users for Trac projects",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['Trac'],
      entry_points = """
      [console_scripts]
      rename-trac-users = renametracusers.main:main
      """,
      )

