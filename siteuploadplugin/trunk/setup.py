#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'siteupload'
VERSION = '0.11'

setup(  name=PACKAGE, version=VERSION,
        author = 'John Hampton',
        author_email = 'pacopablo@pacopablo.com',
        url = 'http://trac-hacks.org/wiki/SiteUploadPlugin',
        description = 'Upload files to trac environment htdocs dir',
        license='BSD',
        zip_safe = True,
        packages = ['siteupload'],
        package_data = { 'siteupload' : ['htdocs/css/*.css', 'htdocs/img/*',
                                        'templates/*.html', ]},
        entry_points = {'trac.plugins': ['siteupload = siteupload']},
)
