from setuptools import find_packages, setup

version='0.5'

setup(name='mail2trac',
      version=version,
      description="mail2trac",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/MailToTracPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'mail2trac': ['templates/*', 'htdocs/*'] },
      zip_safe=False,
      entry_points = """
      [console_scripts]
      mail2trac = mail2trac.email2trac:main

      [trac.plugins]
      email2ticket = mail2trac.email2ticket
      emailposthandler = mail2trac.web
      emailfilters = mail2trac.filters
      """,
      )

