from setuptools import find_packages, setup

version='0.0'

setup(name='ExtendedVersionTracPlugin',
      version=version,
      description="Extend versions in trac",
      author='Malcolm Studd',
      author_email='mestudd@gmail.com',
      url='',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'extendedversion': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      extendedversion.version = extendedversion.version
      extendedversion.milestone = extendedversion.milestone
      extendedversion.environment = extendedversion.environment
      """,
      )

