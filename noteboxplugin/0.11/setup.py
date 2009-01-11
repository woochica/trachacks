#!/usr/bin/python

from notebox import __version__ as VERSION
from setuptools import setup

setup(
    name = 'NoteBox',
    version = VERSION,
    packages = ['notebox'],
    package_data = { 'notebox': ['htdocs/css/*.css', 'htdocs/*.png'] },
    author = 'Bernhard Gruenewaldt',
    author_email = 'trac@gruenewaldt.net',
    maintainer = 'Bernhard Gruenewaldt',
    maintainer_email = 'trac@gruenewaldt.net',
    url = 'http://trac-hacks.org/wiki/NoteBoxPlugin',
    description = 'The NoteBox Plugin for Trac',
    entry_points={'trac.plugins': ['NoteBox = notebox.notebox']},
    keywords = 'trac toc',
    license = 'GPLv2+',
)
