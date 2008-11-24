from setuptools import find_packages, setup

version='0.1'

setup(name='tracblognotifier',
      version=version,
      description="Notification of blog post/comment changes",
      author='Nick Loeve',
      author_email='nick@hyves.nl',
      url='',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'tracblognotifier': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      tracblognotifier = tracblognotifier
      """,
      extras_require={
        'fullblogplugin': "TracFullBlogPlugin>=0.1"
      }
)

