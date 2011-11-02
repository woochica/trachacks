from setuptools import find_packages, setup

version='1'

setup(name='mail2trac',
      version=version,
      description="mail2trac allow to respond to ticket via mail",
      author='Olivier ANDRE',
      author_email='oandre@bearstech.com',
      url='http://trac-hacks.org/wiki/MailToTracPlugin',
      keywords='trac plugin email',
      license="GPLv3",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={ 'mail2trac': ['templates/*', 'htdocs/*'] },
      zip_safe=False,

      entry_points = """
      [trac.plugins]
      mail2trac = mail2trac
      """,
      )

