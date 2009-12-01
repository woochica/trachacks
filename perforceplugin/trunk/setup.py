from setuptools import setup, find_packages


setup(
    name='TracPerforce',
    description='Perforce version control plugin for Trac',
    author='Lewis Baker, Tressieres Thomas',
    author_email='lewisbaker@users.sourceforge.net, thomas.tressieres@free.fr',

    keywords='trac scm plugin perforce p4',
    url='http://trac-hacks.org/wiki/PerforcePlugin',
    version='0.5.0',
    license="""
    Copyright 2006, Maptek Pty Ltd

    This software is provided "as is" with no warranty express or implied.
    Use it at your own risk.

    Permission to use or copy this software for any purpose is granted,
    provided the above notices are retained on all copies.
    """,
    long_description="""
    This Trac 0.11 plugin provides support for the Perforce SCM.
    """,
    zip_safe=True,
    packages=['p4trac'],
    entry_points = {'trac.plugins':
                    ['perforce = p4trac.api'],
                    },
    install_requires=["PyPerforce >=0.4",
                      "PyProtocols >=0.9.3",
                      ],
    )
