from setuptools import find_packages, setup

version='1.1'

setup(name='AdminEnumListPlugin',
      version=version,
      description="Adds drag-and-drop reordering to admin panel enum lists.",
      author='Stepan Riha',
      author_email='trac@nonplus.net',
      url='http://trac-hacks.org/wiki/AdminEnumListPlugin',
      keywords='trac plugin',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'adminenumlistplugin': ['htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      adminenumlistplugin = adminenumlistplugin.adminenumlistplugin
      """,
      )

