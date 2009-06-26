#!/usr/bin/env python
#
# Copyright (c) 2008-2009 The Jira2Trac Project.
# See LICENSE.txt for details.

import os
from setuptools import setup


def get_version():
    """
    Gets the version number. Pulls it from the source files rather than
    duplicating it.
    """
    # we read the file instead of importing it as root sometimes does not
    # have the cwd as part of the PYTHONPATH

    fn = os.path.join(os.getcwd(), 'jira2trac', '__init__.py')
    lines = open(fn, 'rt').readlines()

    version = None

    for l in lines:
        # include the ' =' as __version__ is a part of __all__
        if l.startswith('__version__ =', ):
            x = compile(l, fn, 'single')
            eval(x)
            version = locals()['__version__']
            break

    if version is None:
        raise RuntimeError('Couldn\'t determine version number')

    return '.'.join([str(x) for x in version])


setup(
    name = 'Jira2Trac',
    version = get_version(),
    author = 'Thijs Triemstra',
    author_email = 'thijs@red5.org',
    url = 'http://trac-hacks.org/wiki/JiraToTracIntegration',
    description = 'Tools to migrate from Jira to Trac',
    license = 'MIT License',
    zip_safe=True,
    packages=['jira2trac'],
    package_data={'jira2trac': ['templates/*.html',
                                'templates/*.cfg']},

    install_requires = [
        'trac>=0.11',
    ],

)
