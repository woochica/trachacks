#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracAccountManager',
    version = '0.1.2',
    author = 'Matthew Good',
    author_email = 'trac@matt-good.net',
    url = 'http://trac-hacks.org/wiki/AccountManagerPlugin',
    description = 'User account management plugin for Trac',

    license = '''
"THE BEER-WARE LICENSE" (Revision 42):
<trac@matt-good.net> wrote this file.  As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.   Matthew Good''',

    zip_safe=True,
    packages=['acct_mgr', 'acct_mgr/stores'],
    package_data={'acct_mgr': ['templates/*.cs']},
    
    entry_points = {
        'trac.plugins': [
            'acct_mgr.api = acct_mgt.api',
            'acct_mgr.web_ui = acct_mgr.web_ui',
            'acct_mgr.stores = acct_mgr.stores',
        ],
    },
)

