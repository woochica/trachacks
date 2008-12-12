from setuptools import find_packages, setup

setup(
    name='TicketModifiedFiles',
    version='1.00',
    description='Trac plugin that lists the files that have been modified while resolving a ticket.',
    author='Emilien Klein',
    author_email='Emilien Klein <e2jk AT users DOT sourceforge DOT net>',
    license='BSD-ish (see the COPYING.txt file)',
    url='http://trac-hacks.org/wiki/TicketModifiedFilesPlugin',
    packages=['ticketmodifiedfiles'],
    package_data={'ticketmodifiedfiles': ['templates/*.html', 'htdocs/css/*.css', 'htdocs/js/*.js']},
    install_requires=['Genshi>=0.5'],
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev'],
    entry_points = {'trac.plugins': ['ticketmodifiedfiles = ticketmodifiedfiles']},
)