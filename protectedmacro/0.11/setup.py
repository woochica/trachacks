#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# A python egg can generally be constructed using:
# python setup.py bdist_egg
#

import os

from setuptools import setup

setup(
    name = 'TracProtected',
    version = '2.0.0',
    packages = ['protected'],
    package_data = {"protected":[]},
    author = 'Boudewijn Schoon',
    author_email = 'p.b.schoon@frayja.com',
    description = 'A Trac macro to limit access to parts of a trac page and attachments.',
    long_description = '''With the TracProtected macro it is possible to limit access to parts of a trac page.

    A protected part has the following syntax:
    {{{
    #!protected
    #:This is what an unauthorized user sees (optional)
    This is what an authorized user sees
    }}}

    A protected part can use !protected, !protected-red,
    !protected-blue, or !protected-green to provide access
    restrictions on different levels. Users will only see these
    protected sections when they have the permissions
    "PROTECTED_VIEW", "PROTECTED_RED_VIEW", "PROTECTED_BLUE_VIEW", or
    "PROTECTED_GREEN_VIEW", respectively.

    Attachments are protected when the key-string "!protected",
    "!protected-red", "!protected-blue", or "!protected-green" is
    present in the attachment's description.
    
    To enable the attachment protection the conf/trac.ini must be
    modified. Add the ProtectedAttachmentPolicy to the
    permission_policies:
    [trac]
    permission_policies = ProtectedAttachmentPolicy, DefaultPermissionPolicy    
    ''',
    license = 'BSD',
    keywords = 'trac macro authentication protected access',
    url = '',
    classifiers = ['Framework :: Trac',
                   'Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   ],
    install_requires = ['Trac'],
    entry_points = {'trac.plugins': ['protected.macro = protected.macro',],},
)
