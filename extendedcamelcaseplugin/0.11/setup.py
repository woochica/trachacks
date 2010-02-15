from setuptools import find_packages, setup

version='0.1'

setup(name='extendedcamelcase',
      version=version,
      description="extend camelcase to link to wiki pages",
      author='You(Ricky) Li',
      author_email='You.Li@sixnet.com',
      url='',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'extendedcamelcase': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      extendedcamelcase = extendedcamelcase
      """,
      )

