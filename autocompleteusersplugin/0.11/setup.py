from setuptools import find_packages, setup

version='0.4.1'

setup(name='AutocompleteUsers',
      version=version,
      description="complete the known trac users, AJAX style",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),      
      include_package_data=True,
      package_data={'autocompleteusers': ['htdocs/css/*', 'htdocs/js/*']},
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      autocompleteusers = autocompleteusers
      """,
      )

