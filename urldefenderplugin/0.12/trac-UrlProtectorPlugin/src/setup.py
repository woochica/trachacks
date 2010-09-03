#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

PACKAGE = 'TracUrlDefender'
VERSION = '0.0.1'

setup(
     name = PACKAGE,
     version = VERSION,
 
     author = "Stefano Apostolico",
     author_email = "s.postolico@gmail.com",
     description = "A handler to redirect anonymous requests",
     long_description = """A handler for redirecting all anonymous requests to a\
                            form based authentication handler.  Currently only\
                               supports AccounttManagerPlugin""",
     license = "BSD",
     keywords = "trac plugin authentication required acctmanager",
     url = "http://trac-hacks.org/wiki/UrlDefenderPlugin",
 
     packages = [ 'tracurldefender' ],
 
     entry_points = {'trac.plugins': ['tracurldefender = tracurldefender']},
     #install_requires = [ 'tracaccountmanager' ]
 )
