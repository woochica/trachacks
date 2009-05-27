#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'TracPledgieMacro',
    version = '0.1',
    packages = ['TracPledgieMacro'],
    author = 'Stephan',
    author_email = 'ask me',
    description = "Trac wiki macro to include pledgie fundraising plugin",
    url = 'http://www.trac-hacks.org/wiki/PledgieMacro',
    license = 'GPLv3',
    keywords = 'pledgie, paypal, donate, pledge',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['TracPledgieMacro.macro = TracPledgieMacro.macro']}
)
