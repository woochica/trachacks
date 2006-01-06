from setuptools import setup

PACKAGE = 'TracPyDoc'
VERSION = '0.1'

setup(
    name=PACKAGE,
    version=VERSION,
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    url='http://trac-hacks.swapoff.org/wiki/PyDocPlugin',
    packages=['tracpydoc'],
    package_data={'tracpydoc' : ['templates/*.cs', 'htdocs/css/*.css']}
    )
