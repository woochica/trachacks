from setuptools import find_packages, setup

version='0.0'

setup(name='PdfRendererPlugin',
      version=version,
      description="Render PDF files",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'pdfrendererplugin': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      pdfrendererplugin = pdfrendererplugin
      """,
      )

