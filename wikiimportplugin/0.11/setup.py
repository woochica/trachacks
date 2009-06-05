from setuptools import find_packages, setup

version='0.1'

setup(name='WikiImport',
      version=version,
      description="Makes it possible to import a set of Wiki pages from another Trac instance.",
      author='Tristan Rivoallan',
      author_email='trivoallan@clever-age.com',
      url='http://www.clever-age.org',
      keywords='trac plugin',
      license="GPLv3",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'wikiimport': ['templates/*', 'htdocs/css/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      wikiimport.web_ui = wikiimport.web_ui
      """,
      )

