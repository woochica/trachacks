from setuptools import find_packages, setup

version='0.0'

setup(name='LdapAuthStorePlugin',
      version=version,
      description="LDAP password store for Trac's AccountManager",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      install_requires = [ 'TracAccountManager',
                           'LdapPlugin', ],
      dependency_links = [
        "http://trac-hacks.org/svn/ldapplugin/0.11#egg=LdapPlugin",
        ],
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      ldapauthstore = ldapauthstore
      """,
      )

