# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Dan Ordille <dordille@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='AwesomeAttachmentsPlugin',
    version='0.3',
    author='Dan Ordille',
    author_email='dordille@gmail.com',
    license='3-Clause BSD',
    packages=find_packages(exclude=['*.tests']),
    package_data={ 'awesome': [ 'htdocs/images/*', 'htdocs/js/*', 'htdocs/css/*' ]},
    entry_points = """
        [trac.plugins]
        awesome = awesome.awesomeattachments
    """,
)
