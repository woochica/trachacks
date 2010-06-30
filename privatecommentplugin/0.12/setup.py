from setuptools import find_packages, setup

version='0.1'

setup(name='privatecomments',
      version=version,
      description="A trac plugin that lets you create comments which are only visible for users with a special permission",
      author='Michael Henke',
      author_email='michael.henke@she.de',
      url='',
      keywords='trac plugin security ticket comment group',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      privatecomments = privatecomments
      """,
      )

