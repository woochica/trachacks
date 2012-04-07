from setuptools import find_packages, setup

version='0.1.3'

setup(name='SharedCookieAuth',
      version=version,
      description="share cookies between trac projects in the same directory",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      maintainer='Lars Wireen',
      maintainer_email='lw@agitronic.se',
      url='http://trac-hacks.org/wiki/SharedCookieAuthPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'sharedcookieauth': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      sharedcookieauth = sharedcookieauth
      """,
      )

