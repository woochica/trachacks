from setuptools import setup

install_requires = [
    'Trac',
    'TracAccountManager',
    'python-ldap',
]

setup(
    name='TracLDAPAuth',
    version='1.1',
    packages=['ldapauth'],

    author='Noah Kantrowitz',
    author_email='coderanger@yahoo.com',
    maintainer='Nikolaos Papagrigoriou',
    maintainer_email='nikolaos@papagrigoriou.com',
    description=('An AccountManager password store that uses python-ldap to '
                 'check against an LDAP server.'),
    license='BSD',
    keywords='trac plugin accountmanager',
    url='http://trac-hacks.org/wiki/TracLdapAuthPlugin',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=install_requires,
    entry_points="""\
    [trac.plugins]
    ldapauth.store = ldapauth.store
    """
)
