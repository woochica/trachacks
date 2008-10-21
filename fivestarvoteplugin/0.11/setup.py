# Based on code from : http://trac-hacks.org/wiki/VotePlugin
from setuptools import setup

setup(
    name='FiveStarVote',
    version='0.1',
    packages=['fivestarvote'],
	package_data={'fivestarvote' : ['htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/css/*.png']},
    author='Dav Glass [dav.glass@yahoo.com]',
    license='BSD',
    url='none yet',
    description='A 5 star plugin for voting on Trac resources.',
    entry_points = {'trac.plugins': ['fivestarvote = fivestarvote']},
    )
