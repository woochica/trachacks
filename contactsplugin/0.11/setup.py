#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'contacts'

setup(
    name=PACKAGE,
    description='Plugin which keeps trac of Contact data',
    keywords='trac plugin contact person address addressbook address-book',
    version='0.1',
    url='http://trac-hacks.org/wiki/ContactsPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='CM Lubinski',
    author_email='clubinski@networkninja.com',
    long_description="""
    Adds a new menu item for contacts. Stores this contacts in the db with their first name, last name, position,
    email, and phone.
    """,
    packages=[PACKAGE],
    package_data={PACKAGE : ['templates/*.html', 'htdocs/*']},
    entry_points = {
        'trac.plugins': [
            'contacts.db = contacts.db',
            'contacts.web_ui = contacts.web_ui',
        ]
    })
