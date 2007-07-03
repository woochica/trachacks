#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

PACKAGE = 'TracAuthRequired'
VERSION = '0.3'

setup(
    name = PACKAGE,
    version = VERSION,

    author = "Anton Graham",
    author_email = "bladehawke@gmail.com",
    description = "A handler to redirect anonymous requests",
    long_description = """A handler for redirecting all anonymous requests to a\
                           form based authentication handler.  Currently only\
                              supports AccounttManagerPlugin""",
    license = "BSD",
    keywords = "trac plugin authentication required acctmanager",
    url = "http://trac-hacks.org/wiki/AuthRequiredPlugin",

    packages = [ 'tracauthrequired' ],

    entry_points = {'trac.plugins': ['tracauthrequired = tracauthrequired']},
    install_requires = [ 'tracaccountmanager' ]
)
