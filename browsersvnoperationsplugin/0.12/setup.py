#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='TracBrowserSvnOperations', 
    version='0.1',
    #install_requires='Trac >= 0.12',
    description='Perform certain operations to the Subversion repository from '
                'within the Trac code browser',
    long_description='',
    
    author='',
    author_email='',
    
    url='http://trac-hacks.org/wiki/BrowserSvnOperationsPlugin',
    classifiers=[],
    license='',
    
    packages=['trac_browser_svn_ops'],
    package_data={
        'trac_browser_svn_ops': [
            'templates/*.html',
            'htdocs/js/*.js',
            'htdocs/css/*.css',
            'htdocs/css/smoothness/*.css',
            'htdocs/css/smoothness/images/*.png',
            ]
        },
            
    entry_points = """
        [trac.plugins]
        browserops = trac_browser_svn_ops.browser
    """,
)
