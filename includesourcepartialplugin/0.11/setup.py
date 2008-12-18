from setuptools import setup

setup(name='IncludeSource',
    version='0.1',
    packages=['includesource'],
    author='Chris Heller',
    description='Include (parts of) a source file into the current wiki page',
    url='http://trac-hacks.org/wiki/IncludeSourcePartialPlugin',
    license='BSD',
    install_requires = ['Trac'],
    entry_points = {'trac.plugins': ['includesource.IncludeSource = includesource.IncludeSource']})