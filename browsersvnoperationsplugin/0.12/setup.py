#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='TracBrowserSvnOperations', 
    version='0.1',
    description='Perform certain operations to the Subversion repository from '
                'within the Trac code browser',
    long_description='',
    
    author='',
    author_email='',
    
    url='http://trac-hacks.org/wiki/BrowserSvnOperationsPlugin',
    classifiers=[],
    license='',
    
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        helloworld = trac_browser_svn_ops.helloworld
    """,
)
