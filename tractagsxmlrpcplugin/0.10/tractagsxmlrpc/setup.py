from setuptools import setup

setup(
    name='TragTagsXMLRPC',
    version='0.0.1',
    packages=['tractagsxmlrpc'],
    package_data={'tractags' : ['']},
    author='mike.buzzetti@gmail.com',
    
    description='Plugin for Trac to allow XMLRPC for each tagspace ',
    entry_points = {'trac.plugins': ['tractagsxmlrpc = tractagsxmlrpc']}
    )
