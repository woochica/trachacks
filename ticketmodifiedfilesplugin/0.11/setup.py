from setuptools import find_packages, setup

setup(
    name='TicketModifiedFiles',
    description='Trac plugin that lists the files that have been modified while resolving a ticket.',
    version='0.7',
    license='BSD-ish (see the COPYING.txt file)',
    author='Emilien Klein',
    author_email='Emilien Klein <e2jk AT users DOT sourceforge DOT net>',
    url='http://trac-hacks.org/wiki/TicketModifiedFilesPlugin',
    packages=['ticketmodifiedfiles'],
    entry_points = {'trac.plugins': ['ticketmodifiedfiles = ticketmodifiedfiles']},
    package_data={'ticketmodifiedfiles': ['templates/*.html', 'htdocs/css/*.css']},
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev'],
    install_requires=['Genshi >= 0.5.dev-r698,==dev'],
)