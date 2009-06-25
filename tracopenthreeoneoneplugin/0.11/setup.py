from setuptools import find_packages, setup

version='0.0'

setup(name='TracOpen311',
      version=version,
      description="open 311 for Trac: http://api.dc.gov/open311/v1",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://api.dc.gov/open311/v1',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'tracopen311': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      tracopen311 = tracopen311
      """,
      )

