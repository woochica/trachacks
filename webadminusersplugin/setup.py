#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'WebAdminUsers',
    version = '0.1.0',
    author = 'Jonathan Lange',
    author_email = 'jml@mumak.net',
    description = 'Trac plugin to manage user accounts from web admin',
    license = '''MIT Licence''',
    zip_safe=True,
    entry_points = """
    [trac.plugins]
    WebAdminUsers = acct_admin
    """,
    packages=['acct_admin'],
    package_data={'acct_admin': ['templates/*.cs']})


