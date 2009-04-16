from setuptools import find_packages, setup

version='0.1'

setup(name='CustomFieldProvider',
      version=version,
      description="provide custom ticket fields programmatically",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/CustomFieldProviderPlugin',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'customfieldprovider': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      customfieldprovider = customfieldprovider
      """,
      )

